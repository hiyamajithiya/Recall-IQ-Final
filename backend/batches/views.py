from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, F
import logging
from core.permissions import IsTenantMember, IsTenantOwner, IsTenantStaff
from core.models_recipients import Recipient, ContactGroup
from .models import Batch, BatchGroup, BatchRecord, BatchRecipient
from .serializers import (
    BatchSerializer, BatchCreateSerializer, BatchActionSerializer, 
    BatchRecordSerializer, BatchRecipientSerializer
)
from .tasks import send_batch_emails, execute_batch_subcycle

logger = logging.getLogger(__name__)


class BatchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BatchCreateSerializer
        return BatchSerializer
    
    def get_queryset(self):
        queryset = Batch.objects.select_related('tenant', 'template', 'email_configuration').prefetch_related('batch_groups__group')
        
        if self.request.user.role in ['super_admin', 'support_team']:
            return queryset
        elif self.request.user.role in ['tenant_admin', 'staff_admin'] and self.request.user.tenant:
            queryset = queryset.filter(tenant=self.request.user.tenant)
            return queryset
        elif self.request.user.tenant:
            # For regular staff, filter by tenant
            queryset = queryset.filter(tenant=self.request.user.tenant)
        else:
            return Batch.objects.none()
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.order_by('start_time', '-created_at')  # Upcoming batches first
    
    def perform_update(self, serializer):
        """Handle batch updates with smart status management"""
        from django.utils import timezone
        
        instance = serializer.instance
        updated_data = serializer.validated_data
        
        # Check if start_time is being updated to a future date
        new_start_time = updated_data.get('start_time')
        if new_start_time:
            current_time = timezone.now()
            
            # If batch was completed but start_time is moved to future, reset to scheduled
            if instance.status == 'completed' and new_start_time > current_time:
                instance.status = 'scheduled'
                instance.emails_sent = 0
                instance.emails_failed = 0
                instance.sub_cycles_completed = 0
        
        # Save the instance
        serializer.save()
        
        # Update batch status based on new conditions
        self._update_batch_status_after_edit(serializer.instance)
    
    def _update_batch_status_after_edit(self, batch):
        """Update batch status after editing based on conditions"""
        from django.utils import timezone
        current_time = timezone.now()
        
        # Logic for status transitions after edit
        if batch.status in ['draft', 'scheduled', 'completed']:
            if batch.start_time and batch.email_configuration and batch.email_configuration.is_active:
                if batch.start_time > current_time:
                    batch.status = 'scheduled'
                elif batch.start_time <= current_time:
                    # Don't auto-start, let the scheduled task handle it
                    batch.status = 'scheduled'
                    
                batch.save(update_fields=['status', 'updated_at'])
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsTenantMember()]
        return [IsAuthenticated(), IsTenantMember()]
    
    def perform_create(self, serializer):
        """Add tenant and ensure email configuration is set"""
        tenant = self.request.user.tenant
        instance = serializer.save(tenant=tenant)
        
        # If no email configuration was provided, try to find a default one
        if not instance.email_configuration:
            from core.models import UserEmailConfiguration
            from rest_framework.exceptions import ValidationError
            
            # First try the creating user's default config
            email_config = UserEmailConfiguration.objects.filter(
                user=self.request.user,
                is_active=True,
                is_default=True
            ).first()
            
            # If not found, try tenant creator's default config
            if not email_config and tenant.created_by:
                email_config = UserEmailConfiguration.objects.filter(
                    user=tenant.created_by,
                    is_active=True,
                    is_default=True
                ).first()
                
            # If still no config, try any active config from tenant admin users
            if not email_config:
                tenant_admin_configs = UserEmailConfiguration.objects.filter(
                    user__tenant=tenant,
                    user__role__in=['tenant_admin', 'staff_admin'],
                    is_active=True
                ).first()
                if tenant_admin_configs:
                    email_config = tenant_admin_configs
            
            # Update the batch if we found a working config
            if email_config:
                instance.email_configuration = email_config
                
                # Auto-set status to scheduled if start_time is valid
                if instance.start_time and instance.start_time > timezone.now():
                    instance.status = 'scheduled'
                    
                instance.save(update_fields=['email_configuration', 'status'])
            else:
                raise ValidationError({
                    'email_configuration': 'No active email configuration found. Please configure an email provider in settings before creating a batch.'
                })
        else:
            # Email configuration exists, check if we should auto-schedule
            if (instance.email_configuration.is_active and 
                instance.start_time and 
                instance.start_time > timezone.now()):
                instance.status = 'scheduled'
                instance.save(update_fields=['status'])

    @action(detail=True, methods=['get'])
    def recipients(self, request, pk=None):
        """Get all recipients for a batch with their document status (both new and legacy systems)"""
        batch = self.get_object()
        
        # Combine both new batch recipients and legacy group emails
        recipients_data = []
        
        # Get new system recipients (BatchRecipient)
        batch_recipients = batch.batch_recipients.all()
        for batch_recipient in batch_recipients:
            recipients_data.append({
                'id': batch_recipient.id,
                'recipient_id': batch_recipient.recipient.id,  # Add the actual recipient ID
                'recipient_name': batch_recipient.recipient.name,
                'recipient_email': batch_recipient.recipient.email,
                'organization': batch_recipient.recipient.organization_name,
                'documents_received': batch_recipient.documents_received,
                'email_sent': batch_recipient.email_sent,
                'emails_sent_count': batch_recipient.emails_sent_count,
                'last_email_sent_at': batch_recipient.last_email_sent_at,
                'is_completed': batch_recipient.is_completed,
                'completed_at': batch_recipient.completed_at,
                'source': 'new_system'
            })
        
        # Get legacy system recipients (Group -> GroupEmail)
        for batch_group in batch.batch_groups.all():
            group_emails = batch_group.group.group_emails.filter(is_active=True)
            for group_email in group_emails:
                # Get corresponding batch record if exists
                try:
                    batch_record = BatchRecord.objects.get(
                        batch=batch,
                        recipient_email=group_email.email
                    )
                    documents_received = batch_record.document_received
                    email_sent = batch_record.marked_done
                except BatchRecord.DoesNotExist:
                    documents_received = False
                    email_sent = False
                
                # For legacy system, try to find corresponding Recipient by email
                # If not found, use a special identifier
                from core.models import Recipient
                try:
                    recipient = Recipient.objects.get(email=group_email.email, tenant=batch.tenant)
                    recipient_id = recipient.id
                except Recipient.DoesNotExist:
                    # For legacy emails without corresponding Recipients, 
                    # we'll use a special identifier that the mark_documents_received can handle
                    recipient_id = f"legacy_{group_email.id}"
                
                recipients_data.append({
                    'id': f"legacy_{group_email.id}",
                    'recipient_id': recipient_id,  # Add recipient ID for legacy system
                    'recipient_name': group_email.name,
                    'recipient_email': group_email.email,
                    'organization': getattr(group_email, 'organization', ''),
                    'documents_received': documents_received,
                    'email_sent': email_sent,
                    'emails_sent_count': 1 if email_sent else 0,
                    'last_email_sent_at': batch_record.created_at if email_sent and 'batch_record' in locals() else None,
                    'is_completed': documents_received,
                    'completed_at': batch_record.updated_at if documents_received and 'batch_record' in locals() else None,
                    'source': 'legacy_system'
                })
        
        # Apply filters
        documents_received = request.query_params.get('documents_received')
        if documents_received is not None:
            filter_value = documents_received.lower() == 'true'
            recipients_data = [r for r in recipients_data if r['documents_received'] == filter_value]
        
        email_sent = request.query_params.get('email_sent')
        if email_sent is not None:
            filter_value = email_sent.lower() == 'true'
            recipients_data = [r for r in recipients_data if r['email_sent'] == filter_value]
        
        # Apply search
        search = request.query_params.get('search')
        if search:
            search_lower = search.lower()
            recipients_data = [
                r for r in recipients_data 
                if (search_lower in r['recipient_name'].lower() if r['recipient_name'] else False) or
                   (search_lower in r['recipient_email'].lower() if r['recipient_email'] else False) or
                   (search_lower in r['organization'].lower() if r['organization'] else False)
            ]
        
        # Manual pagination (since we're combining data sources)
        page_size = self.paginate_queryset([])  # Get page size from paginator
        page_size = getattr(self.paginator, 'page_size', 10)
        page_number = int(request.query_params.get('page', 1))
        
        total_count = len(recipients_data)
        start_index = (page_number - 1) * page_size
        end_index = start_index + page_size
        paginated_data = recipients_data[start_index:end_index]
        
        # Return paginated response in DRF format
        return Response({
            'count': total_count,
            'next': f"?page={page_number + 1}" if end_index < total_count else None,
            'previous': f"?page={page_number - 1}" if page_number > 1 else None,
            'results': paginated_data
        })

    @action(detail=True, methods=['post'])
    def update_recipients(self, request, pk=None):
        """Update batch recipients"""
        batch = self.get_object()
        
        recipient_ids = request.data.get('recipient_ids', [])
        contact_group_ids = request.data.get('contact_group_ids', [])
        
        # Clear existing recipients that haven't been sent emails
        BatchRecipient.objects.filter(batch=batch, email_sent=False).delete()
        
        # Add new recipients
        recipients = None
        if recipient_ids:
            recipients = Recipient.objects.filter(
                id__in=recipient_ids,
                tenant=request.user.tenant
            )
        
        contact_groups = None
        if contact_group_ids:
            contact_groups = ContactGroup.objects.filter(
                id__in=contact_group_ids,
                tenant=request.user.tenant
            )
        
        batch.add_recipients(recipients=recipients, contact_groups=contact_groups)
        
        return Response({
            'message': 'Recipients updated successfully',
            'total_recipients': batch.total_recipients
        })

    @action(detail=True, methods=['post'])
    def mark_documents_received(self, request, pk=None):
        """Mark documents as received for specific recipients"""
        batch = self.get_object()
        recipient_ids = request.data.get('recipient_ids', [])
        
        if not recipient_ids:
            return Response(
                {'error': 'Please provide recipient_ids'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Separate regular recipient IDs from legacy IDs
        regular_recipient_ids = []
        legacy_ids = []
        
        for recipient_id in recipient_ids:
            if isinstance(recipient_id, str) and recipient_id.startswith('legacy_'):
                legacy_ids.append(recipient_id)
            else:
                regular_recipient_ids.append(recipient_id)
        
        updated_count = 0
        updated_logs_count = 0
        
        # Handle regular recipients (new system)
        if regular_recipient_ids:
            batch_recipients = batch.batch_recipients.filter(
                recipient_id__in=regular_recipient_ids,
                is_completed=False
            )
            
            for batch_recipient in batch_recipients:
                batch_recipient.mark_completed(request.user)
                updated_count += 1
            
            # Update email logs for regular recipients
            from logs.models import EmailLog
            email_logs = EmailLog.objects.filter(
                batch=batch,
                batch_recipient__recipient_id__in=regular_recipient_ids,
                documents_received=False
            )
            
            for log in email_logs:
                log.mark_documents_received(request.user)
                updated_logs_count += 1
        
        # Handle legacy recipients (legacy system)
        if legacy_ids:
            # Extract group email IDs from legacy identifiers
            group_email_ids = [int(leg_id.replace('legacy_', '')) for leg_id in legacy_ids if leg_id.replace('legacy_', '').isdigit()]
            
            if group_email_ids:
                # Update BatchRecord for legacy system
                from .models import BatchRecord
                from tenants.models import GroupEmail
                
                for group_email_id in group_email_ids:
                    try:
                        group_email = GroupEmail.objects.get(id=group_email_id)
                        batch_record, created = BatchRecord.objects.get_or_create(
                            batch=batch,
                            recipient_email=group_email.email,
                            defaults={
                                'document_received': True,
                                'marked_done': True
                            }
                        )
                        if not created and not batch_record.document_received:
                            batch_record.document_received = True
                            batch_record.save()
                            updated_count += 1
                        elif created:
                            updated_count += 1
                    except GroupEmail.DoesNotExist:
                        continue
        
        # Check if batch should auto-complete
        if batch.should_auto_complete():
            batch.status = 'completed'
            batch.save()
        
        return Response({
            'message': f'Marked {updated_count} recipients as documents received',
            'updated_count': updated_count,
            'updated_logs': updated_logs_count,
            'batch_completed': batch.status == 'completed'
        })

    @action(detail=True, methods=['post'])
    def mark_documents_not_received(self, request, pk=None):
        """Mark documents as not received for specific recipients"""
        batch = self.get_object()
        recipient_ids = request.data.get('recipient_ids', [])
        
        if not recipient_ids:
            return Response(
                {'error': 'Please provide recipient_ids'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Separate regular recipient IDs from legacy IDs
        regular_recipient_ids = []
        legacy_ids = []
        
        for recipient_id in recipient_ids:
            if isinstance(recipient_id, str) and recipient_id.startswith('legacy_'):
                legacy_ids.append(recipient_id)
            else:
                regular_recipient_ids.append(recipient_id)
        
        updated_count = 0
        updated_logs_count = 0
        
        # Handle regular recipients (new system)
        if regular_recipient_ids:
            # Update batch recipients
            updated = batch.batch_recipients.filter(
                recipient_id__in=regular_recipient_ids,
                documents_received=True
            ).update(
                documents_received=False
            )
            updated_count += updated
            
            # Update email logs
            from logs.models import EmailLog
            updated_logs = EmailLog.objects.filter(
                batch=batch,
                batch_recipient__recipient_id__in=regular_recipient_ids,
                documents_received=True
            ).update(
                documents_received=False,
                documents_received_at=None,
                documents_received_by=None
            )
            updated_logs_count += updated_logs
        
        # Handle legacy recipients (legacy system)
        if legacy_ids:
            # Extract group email IDs from legacy identifiers
            group_email_ids = [int(leg_id.replace('legacy_', '')) for leg_id in legacy_ids if leg_id.replace('legacy_', '').isdigit()]
            
            if group_email_ids:
                # Update BatchRecord for legacy system
                from .models import BatchRecord
                from tenants.models import GroupEmail
                
                for group_email_id in group_email_ids:
                    try:
                        group_email = GroupEmail.objects.get(id=group_email_id)
                        try:
                            batch_record = BatchRecord.objects.get(
                                batch=batch,
                                recipient_email=group_email.email
                            )
                            if batch_record.document_received:
                                batch_record.document_received = False
                                batch_record.save()
                                updated_count += 1
                        except BatchRecord.DoesNotExist:
                            # If no record exists, no need to mark as not received
                            pass
                    except GroupEmail.DoesNotExist:
                        continue
        
        return Response({
            'message': f'Marked {updated_count} recipients as documents not received',
            'updated_count': updated_count,
            'updated_logs': updated_logs_count
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Use the main BatchSerializer for the response
        batch = serializer.instance
        response_serializer = BatchSerializer(batch, context=self.get_serializer_context())
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'])
    def execute_action(self, request, pk=None):
        batch = self.get_object()
        serializer = BatchActionSerializer(data=request.data, context={'batch': batch})
        
        if serializer.is_valid():
            action_type = serializer.validated_data['action']
            
            if action_type == 'start':
                # Validate email configuration before starting
                if not batch.email_configuration or not batch.email_configuration.is_active:
                    return Response({
                        'error': 'No active email configuration found for this batch. Please configure email settings first.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                batch.status = 'scheduled'
                if batch.start_time <= timezone.now():
                    if batch.sub_cycle_enabled:
                        # Use new sub-cycle system
                        execute_batch_subcycle.delay(batch.id)
                    else:
                        # Use legacy system
                        send_batch_emails.delay(batch.id)
                
            elif action_type == 'pause':
                batch.status = 'paused'
                
            elif action_type == 'resume':
                # Validate email configuration before resuming
                if not batch.email_configuration or not batch.email_configuration.is_active:
                    return Response({
                        'error': 'No active email configuration found for this batch. Please configure email settings first.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                batch.status = 'scheduled'
                if batch.start_time <= timezone.now():
                    if batch.sub_cycle_enabled:
                        # Use new sub-cycle system
                        execute_batch_subcycle.delay(batch.id)
                    else:
                        # Use legacy system
                        send_batch_emails.delay(batch.id)
                
            elif action_type == 'cancel':
                batch.status = 'cancelled'
            
            batch.save()
            
            return Response({
                'message': f'Batch {action_type}ed successfully',
                'status': batch.status
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reset_documents(self, request, pk=None):
        """Reset document received status for all recipients when editing batch"""
        batch = self.get_object()
        
        reset_documents = request.data.get('reset_documents', False)
        
        if reset_documents:
            # Reset all document statuses in new system
            reset_count = 0
            
            # Reset BatchRecipient statuses
            batch_recipients = batch.batch_recipients.filter(is_completed=True)
            for br in batch_recipients:
                br.is_completed = False
                br.documents_received = False
                br.completed_at = None
                br.next_email_due_at = batch.start_time  # Reset for next cycle
                br.save()
                reset_count += 1
            
            # Reset EmailLog statuses
            from logs.models import EmailLog
            email_logs = EmailLog.objects.filter(
                batch=batch,
                documents_received=True
            )
            for log in email_logs:
                log.documents_received = False
                log.documents_received_at = None
                log.documents_received_by = None
                log.save()
            
            # Reset legacy system if exists
            from .models import BatchRecord
            BatchRecord.objects.filter(
                batch=batch,
                document_received=True
            ).update(
                document_received=False,
                marked_done=False
            )
            
            return Response({
                'message': f'Document status reset for {reset_count} recipients',
                'reset_count': reset_count
            })
        else:
            return Response({
                'message': 'Documents will only be sent to recipients who have not submitted documents',
                'reset_count': 0
            })
    
    
    @action(detail=True, methods=['post'])
    def generate_recipients(self, request, pk=None):
        batch = self.get_object()
        
        if batch.status not in ['draft', 'scheduled']:
            return Response(
                {'error': 'Cannot generate recipients for batch in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        BatchRecord.objects.filter(batch=batch).delete()
        
        created_count = 0
        for batch_group in batch.batch_groups.all():
            group_emails = batch_group.group.group_emails.filter(is_active=True)
            
            for group_email in group_emails:
                BatchRecord.objects.get_or_create(
                    batch=batch,
                    recipient_email=group_email.email,
                    defaults={'recipient_name': group_email.name}
                )
                created_count += 1
        
        batch.total_recipients = created_count
        batch.save()
        
        return Response({
            'message': f'Generated {created_count} recipient records',
            'total_recipients': created_count
        })
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        batch = self.get_object()
        
        total_recipients = batch.total_recipients
        emails_sent = batch.emails_sent
        emails_failed = batch.emails_failed
        pending = total_recipients - emails_sent - emails_failed
        
        stats = {
            'total_recipients': total_recipients,
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
            'emails_pending': pending,
            'success_rate': (emails_sent / total_recipients * 100) if total_recipients > 0 else 0,
            'completion_rate': ((emails_sent + emails_failed) / total_recipients * 100) if total_recipients > 0 else 0
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        queryset = self.get_queryset()
        
        stats = {
            'total_batches': queryset.count(),
            'active_batches': queryset.filter(status__in=['scheduled', 'running']).count(),
            'completed_batches': queryset.filter(status='completed').count(),
            'failed_batches': queryset.filter(status='failed').count(),
            'total_emails_sent': sum(batch.emails_sent for batch in queryset),
            'total_emails_failed': sum(batch.emails_failed for batch in queryset),
        }
        
        recent_batches = queryset[:5]
        stats['recent_batches'] = BatchSerializer(recent_batches, many=True).data
        
        return Response(stats)
    
    def _calculate_total_recipients(self, batch):
        total = 0
        for batch_group in batch.batch_groups.all():
            total += batch_group.group.group_emails.filter(is_active=True).count()
        return total


# Role-based ViewSets for batch management
class TenantAdminBatchViewSet(BatchViewSet):
    """Batches ViewSet for Tenant Admins with full tenant access"""
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        queryset = Batch.objects.select_related('tenant', 'template', 'email_configuration').prefetch_related('batch_groups__group')
        
        if self.request.user.role in ['super_admin', 'support_team']:
            return queryset
        elif self.request.user.tenant:
            queryset = queryset.filter(tenant=self.request.user.tenant)
        else:
            return Batch.objects.none()
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')


class TenantStaffBatchViewSet(BatchViewSet):
    """Batches ViewSet for Tenant Staff with limited access"""
    permission_classes = [IsAuthenticated, IsTenantStaff]
    
    def get_queryset(self):
        queryset = Batch.objects.select_related('tenant', 'template', 'email_configuration').prefetch_related('batch_groups__group')
        
        if self.request.user.role in ['super_admin', 'support_team']:
            return queryset
        elif self.request.user.tenant:
            queryset = queryset.filter(tenant=self.request.user.tenant)
        else:
            return Batch.objects.none()
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_permissions(self):
        # Staff have read-only access by default, but can update document status
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsTenantMember()]
        return [IsAuthenticated(), IsTenantStaff()]


# =============================================================================
# 🚀 ENHANCED BATCH FUNCTIONALITY - MERGED FROM enhanced_views.py
# =============================================================================

from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTenantMember])
def duplicate_batch(request, batch_id):
    """
    🔄 Smart Batch Duplication with Enhancement Options
    
    POST /api/batches/{batch_id}/duplicate/
    
    Request Body (optional):
    {
        "name": "New Batch Name",
        "copy_recipients": true,
        "copy_schedule": false,
        "auto_optimize": true
    }
    
    Creates a duplicate batch with smart defaults and optimization suggestions
    """
    try:
        # Get original batch
        original_batch = Batch.objects.select_related('template', 'tenant', 'email_configuration').get(
            id=batch_id,
            tenant=getattr(request.user, 'tenant', None)
        )
        
        # Parse request options
        options = request.data
        copy_recipients = options.get('copy_recipients', True)
        copy_schedule = options.get('copy_schedule', False)
        auto_optimize = options.get('auto_optimize', True)
        
        with transaction.atomic():
            # Create new batch
            new_batch = Batch.objects.create(
                tenant=original_batch.tenant,
                template=original_batch.template,
                email_configuration=original_batch.email_configuration,
                name=options.get('name', f"{original_batch.name} (Copy)"),
                description=f"Duplicate of: {original_batch.description}",
                status='draft',
                start_time=original_batch.start_time if copy_schedule else timezone.now() + timedelta(hours=1),
                end_time=original_batch.end_time if copy_schedule else None,
                interval_minutes=original_batch.interval_minutes,
                email_support_fields=original_batch.email_support_fields,
                sub_cycle_enabled=original_batch.sub_cycle_enabled,
                sub_cycle_interval=original_batch.sub_cycle_interval,
                sub_cycle_count=original_batch.sub_cycle_count,
                sub_cycle_gap_days=original_batch.sub_cycle_gap_days
            )
            
            # Copy recipients if requested
            recipients_copied = 0
            if copy_recipients:
                # Copy BatchGroups
                for batch_group in original_batch.batch_groups.all():
                    BatchGroup.objects.create(
                        batch=new_batch,
                        group=batch_group.group
                    )
                
                # Copy BatchRecipients
                for batch_recipient in original_batch.batch_recipients.all():
                    BatchRecipient.objects.create(
                        batch=new_batch,
                        recipient=batch_recipient.recipient
                    )
                    recipients_copied += 1
                
                # Update recipient count
                new_batch.total_recipients = recipients_copied
                new_batch.save()
            
            # Generate AI optimization suggestions if requested
            suggestions = []
            if auto_optimize and recipients_copied > 0:
                try:
                    # Get recipient emails for analysis
                    recipient_emails = []
                    for batch_recipient in new_batch.batch_recipients.select_related('recipient').all():
                        recipient_emails.append(batch_recipient.recipient.email)
                    
                    # AI analysis
                    from .ai_analytics import PredictiveAnalytics, DomainReputationAnalyzer
                    predictor = PredictiveAnalytics(new_batch.tenant.id)
                    batch_data = {
                        'recipient_count': recipients_copied,
                        'scheduled_time': new_batch.start_time,
                        'subject': getattr(new_batch.template, 'subject', ''),
                        'content': getattr(new_batch.template, 'content', '')
                    }
                    
                    prediction = predictor.predict_batch_success_rate(batch_data)
                    suggestions = prediction.get('optimization_suggestions', [])
                    
                    # Domain analysis
                    if recipient_emails:
                        domain_analyzer = DomainReputationAnalyzer()
                        domain_analysis = domain_analyzer.analyze_recipient_domains(recipient_emails)
                        suggestions.extend(domain_analysis.get('recommendations', []))
                    
                except Exception as e:
                    logger.error(f"AI optimization failed: {str(e)}")
        
        serializer = BatchSerializer(new_batch)
        
        return Response({
            'success': True,
            'data': {
                'batch': serializer.data,
                'recipients_copied': recipients_copied,
                'ai_suggestions': suggestions if auto_optimize else [],
                'optimization_enabled': auto_optimize
            },
            'message': f'✅ Batch duplicated successfully with {recipients_copied} recipients'
        })
        
    except Batch.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Batch not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Batch duplication error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to duplicate batch'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTenantMember])
def pause_batch(request, batch_id):
    """
    ⏸️ Smart Batch Pause with Status Management
    
    POST /api/batches/{batch_id}/pause/
    
    Safely pauses a running batch with proper status tracking
    """
    try:
        batch = Batch.objects.get(
            id=batch_id,
            tenant=getattr(request.user, 'tenant', None)
        )
        
        if batch.status != 'running':
            return Response({
                'success': False,
                'error': f'Cannot pause batch with status: {batch.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update status atomically
        with transaction.atomic():
            batch.status = 'paused'
            batch.updated_at = timezone.now()
            batch.save(update_fields=['status', 'updated_at'])
        
        logger.info(f"Batch {batch_id} paused by user {request.user.id}")
        
        return Response({
            'success': True,
            'data': {
                'batch_id': batch_id,
                'status': 'paused',
                'paused_at': timezone.now().isoformat()
            },
            'message': '⏸️ Batch paused successfully'
        })
        
    except Batch.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Batch not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Batch pause error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to pause batch'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTenantMember])
def resume_batch(request, batch_id):
    """
    ▶️ Smart Batch Resume with Validation
    
    POST /api/batches/{batch_id}/resume/
    
    Safely resumes a paused batch with validation checks
    """
    try:
        batch = Batch.objects.get(
            id=batch_id,
            tenant=getattr(request.user, 'tenant', None)
        )
        
        if batch.status != 'paused':
            return Response({
                'success': False,
                'error': f'Cannot resume batch with status: {batch.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate batch can be resumed
        if not batch.email_configuration or not batch.email_configuration.is_active:
            return Response({
                'success': False,
                'error': 'Email configuration is not active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update status and trigger processing
        with transaction.atomic():
            batch.status = 'running'
            batch.updated_at = timezone.now()
            batch.save(update_fields=['status', 'updated_at'])
            
            # Queue batch for processing
            send_batch_emails.delay(batch_id)
        
        logger.info(f"Batch {batch_id} resumed by user {request.user.id}")
        
        return Response({
            'success': True,
            'data': {
                'batch_id': batch_id,
                'status': 'running',
                'resumed_at': timezone.now().isoformat()
            },
            'message': '▶️ Batch resumed successfully'
        })
        
    except Batch.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Batch not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Batch resume error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to resume batch'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTenantMember])
def cancel_batch(request, batch_id):
    """
    ❌ Smart Batch Cancellation with Cleanup
    
    POST /api/batches/{batch_id}/cancel/
    
    Request Body (optional):
    {
        "reason": "User requested cancellation",
        "cleanup_logs": true
    }
    
    Safely cancels a batch with optional cleanup
    """
    try:
        batch = Batch.objects.get(
            id=batch_id,
            tenant=getattr(request.user, 'tenant', None)
        )
        
        if batch.status in ['completed', 'cancelled']:
            return Response({
                'success': False,
                'error': f'Cannot cancel batch with status: {batch.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason', 'Cancelled by user')
        cleanup_logs = request.data.get('cleanup_logs', False)
        
        # Update status atomically
        with transaction.atomic():
            batch.status = 'cancelled'
            batch.updated_at = timezone.now()
            
            # Store cancellation reason
            if not batch.email_support_fields:
                batch.email_support_fields = {}
            batch.email_support_fields['cancellation_reason'] = reason
            batch.email_support_fields['cancelled_by'] = request.user.id
            batch.email_support_fields['cancelled_at'] = timezone.now().isoformat()
            
            batch.save(update_fields=['status', 'updated_at', 'email_support_fields'])
            
            # Optional cleanup
            if cleanup_logs:
                from logs.models import EmailLog
                EmailLog.objects.filter(
                    tenant_id=batch.tenant.id,
                    batch_id=batch_id,
                    status='pending'
                ).delete()
        
        logger.info(f"Batch {batch_id} cancelled by user {request.user.id}: {reason}")
        
        return Response({
            'success': True,
            'data': {
                'batch_id': batch_id,
                'status': 'cancelled',
                'reason': reason,
                'cancelled_at': timezone.now().isoformat()
            },
            'message': '❌ Batch cancelled successfully'
        })
        
    except Batch.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Batch not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Batch cancellation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to cancel batch'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTenantMember])
def batch_analytics_summary(request, batch_id):
    """
    📊 Enhanced Batch Analytics Summary
    
    GET /api/batches/{batch_id}/analytics/
    
    Returns comprehensive analytics for a specific batch
    """
    try:
        batch = Batch.objects.select_related('template', 'tenant').get(
            id=batch_id,
            tenant=getattr(request.user, 'tenant', None)
        )
        
        # Basic metrics
        total_recipients = batch.total_recipients or 0
        emails_sent = batch.emails_sent or 0
        emails_failed = batch.emails_failed or 0
        total_processed = emails_sent + emails_failed
        
        # Calculate rates
        success_rate = (emails_sent / total_processed * 100) if total_processed > 0 else 0
        completion_rate = (total_processed / total_recipients * 100) if total_recipients > 0 else 0
        
        # Get email logs for detailed analytics
        from logs.models import EmailLog
        email_logs = EmailLog.objects.filter(
            tenant_id=batch.tenant.id,
            batch_id=batch_id
        ).values('status', 'opened_at', 'clicked_at', 'created_at')
        
        # Calculate engagement metrics
        opened_count = len([log for log in email_logs if log['opened_at']])
        clicked_count = len([log for log in email_logs if log['clicked_at']])
        
        open_rate = (opened_count / emails_sent * 100) if emails_sent > 0 else 0
        click_rate = (clicked_count / emails_sent * 100) if emails_sent > 0 else 0
        
        # Time-based analysis
        if email_logs:
            send_times = [log['created_at'] for log in email_logs if log['created_at']]
            if send_times:
                duration = (max(send_times) - min(send_times)).total_seconds() / 60  # minutes
            else:
                duration = 0
        else:
            duration = 0
        
        # Performance classification
        performance_score = (success_rate * 0.4) + (open_rate * 0.3) + (click_rate * 0.3)
        
        if performance_score >= 80:
            performance_grade = 'Excellent'
        elif performance_score >= 60:
            performance_grade = 'Good'
        elif performance_score >= 40:
            performance_grade = 'Average'
        else:
            performance_grade = 'Needs Improvement'
        
        # Status timeline
        status_timeline = [
            {
                'status': 'created',
                'timestamp': batch.created_at.isoformat(),
                'description': 'Batch created'
            },
            {
                'status': batch.status,
                'timestamp': batch.updated_at.isoformat(),
                'description': f'Current status: {batch.get_status_display()}'
            }
        ]
        
        analytics_data = {
            'batch_info': {
                'id': batch.id,
                'name': batch.name,
                'status': batch.status,
                'created_at': batch.created_at.isoformat(),
                'updated_at': batch.updated_at.isoformat()
            },
            'metrics': {
                'total_recipients': total_recipients,
                'emails_sent': emails_sent,
                'emails_failed': emails_failed,
                'success_rate': round(success_rate, 2),
                'completion_rate': round(completion_rate, 2),
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2),
                'duration_minutes': round(duration, 2)
            },
            'performance': {
                'score': round(performance_score, 2),
                'grade': performance_grade,
                'opened_emails': opened_count,
                'clicked_emails': clicked_count
            },
            'timeline': status_timeline,
            'recommendations': _generate_batch_recommendations(batch, success_rate, open_rate, click_rate)
        }
        
        return Response({
            'success': True,
            'data': analytics_data,
            'message': '📊 Batch analytics generated successfully'
        })
        
    except Batch.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Batch not found or access denied'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Batch analytics error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to generate batch analytics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTenantMember])
def batch_dashboard_overview(request):
    """
    🎯 Enhanced Batch Dashboard Overview
    
    GET /api/batches/dashboard/overview/
    
    Returns comprehensive dashboard data for batch management
    """
    try:
        tenant = getattr(request.user, 'tenant', None)
        if not tenant:
            return Response({
                'success': False,
                'error': 'Tenant not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Time filters
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Basic counts
        total_batches = Batch.objects.filter(tenant=tenant).count()
        active_batches = Batch.objects.filter(tenant=tenant, status__in=['running', 'scheduled']).count()
        completed_batches = Batch.objects.filter(tenant=tenant, status='completed').count()
        failed_batches = Batch.objects.filter(tenant=tenant, status='failed').count()
        
        # Recent activity (last 7 days)
        recent_batches = Batch.objects.filter(
            tenant=tenant,
            created_at__date__gte=week_ago
        ).count()
        
        # Performance metrics
        from django.db.models import Sum, Avg
        completed_batch_stats = Batch.objects.filter(
            tenant=tenant,
            status='completed'
        ).aggregate(
            total_sent=Sum('emails_sent'),
            total_failed=Sum('emails_failed'),
            avg_recipients=Avg('total_recipients')
        )
        
        total_sent = completed_batch_stats['total_sent'] or 0
        total_failed = completed_batch_stats['total_failed'] or 0
        avg_recipients = completed_batch_stats['avg_recipients'] or 0
        
        overall_success_rate = (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0
        
        # Status distribution
        status_distribution = {}
        for status_choice in Batch.STATUS_CHOICES:
            status_key = status_choice[0]
            count = Batch.objects.filter(tenant=tenant, status=status_key).count()
            status_distribution[status_key] = {
                'count': count,
                'label': status_choice[1]
            }
        
        # Recent batches (last 10)
        recent_batch_list = Batch.objects.filter(tenant=tenant).select_related('template').order_by('-created_at')[:10]
        recent_batches_data = []
        
        for batch in recent_batch_list:
            success_rate = 0
            if batch.emails_sent and (batch.emails_sent + (batch.emails_failed or 0)) > 0:
                success_rate = (batch.emails_sent / (batch.emails_sent + (batch.emails_failed or 0))) * 100
            
            recent_batches_data.append({
                'id': batch.id,
                'name': batch.name,
                'status': batch.status,
                'created_at': batch.created_at.isoformat(),
                'total_recipients': batch.total_recipients,
                'success_rate': round(success_rate, 1)
            })
        
        dashboard_data = {
            'summary': {
                'total_batches': total_batches,
                'active_batches': active_batches,
                'completed_batches': completed_batches,
                'failed_batches': failed_batches,
                'recent_activity': recent_batches
            },
            'performance': {
                'overall_success_rate': round(overall_success_rate, 2),
                'total_emails_sent': total_sent,
                'total_emails_failed': total_failed,
                'average_recipients_per_batch': round(avg_recipients, 1)
            },
            'status_distribution': status_distribution,
            'recent_batches': recent_batches_data,
            'quick_actions': [
                {
                    'action': 'create_batch',
                    'label': 'Create New Batch',
                    'icon': '➕',
                    'url': '/api/batches/'
                },
                {
                    'action': 'duplicate_best',
                    'label': 'Duplicate Best Performing',
                    'icon': '🔄',
                    'description': 'Duplicate your best performing batch'
                },
                {
                    'action': 'analytics',
                    'label': 'View AI Analytics',
                    'icon': '🤖',
                    'url': '/api/batches/ai-analytics/dashboard/'
                }
            ]
        }
        
        return Response({
            'success': True,
            'data': dashboard_data,
            'message': '🎯 Dashboard overview generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Dashboard overview error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to generate dashboard overview'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='automation/status')
    def automation_status(self, request):
        """Get automation status and activity logs"""
        try:
            from django_celery_beat.models import PeriodicTask
            from django.core.cache import cache
            
            # Check if recurring batch task is enabled
            task_enabled = False
            last_run = None
            try:
                periodic_task = PeriodicTask.objects.get(name='recurring-batch-processing')
                task_enabled = periodic_task.enabled
                last_run = periodic_task.last_run_at
            except PeriodicTask.DoesNotExist:
                pass
            
            # Get activity logs from cache
            activity_logs = cache.get('batch_automation_logs', [])
            
            # Determine status
            if task_enabled:
                status_text = "Active - Monitoring scheduled batches"
                if last_run:
                    from django.utils import timezone
                    time_diff = timezone.now() - last_run
                    if time_diff.total_seconds() < 3600:  # Less than 1 hour
                        status_text = "Active - Recently processed"
                    elif time_diff.total_seconds() > 86400:  # More than 1 day
                        status_text = "Active - No recent activity"
            else:
                status_text = "Inactive"
            
            last_activity = "No recent activity"
            if last_run:
                last_activity = f"Last run: {last_run.strftime('%Y-%m-%d %H:%M:%S')}"
            
            return Response({
                'enabled': task_enabled,
                'status': status_text,
                'last_activity': last_activity,
                'activity_logs': activity_logs[-10:],  # Last 10 logs
                'last_run': last_run.isoformat() if last_run else None
            })
            
        except Exception as e:
            logger.error(f"Automation status error: {str(e)}")
            return Response({
                'enabled': False,
                'status': 'Unknown',
                'last_activity': 'Error checking status',
                'activity_logs': [],
                'error': str(e)
            })

    @action(detail=False, methods=['post'], url_path='automation/enable')
    def enable_automation(self, request):
        """Enable batch automation"""
        try:
            from django_celery_beat.models import PeriodicTask, CrontabSchedule
            from django.core.cache import cache
            
            # Create or enable the periodic task
            crontab, created = CrontabSchedule.objects.get_or_create(
                minute='0',  # Every hour at minute 0
                hour='*',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*'
            )
            
            periodic_task, created = PeriodicTask.objects.get_or_create(
                name='recurring-batch-processing',
                defaults={
                    'task': 'batches.tasks.schedule_recurring_batches',
                    'crontab': crontab,
                    'enabled': True
                }
            )
            
            if not created:
                periodic_task.enabled = True
                periodic_task.save()
            
            # Log activity
            activity_logs = cache.get('batch_automation_logs', [])
            activity_logs.append(f"{timezone.now().strftime('%H:%M:%S')} - Automation enabled by {request.user.username}")
            cache.set('batch_automation_logs', activity_logs[-50:], 86400)  # Keep 50 logs for 24 hours
            
            return Response({
                'success': True,
                'message': 'Batch automation enabled successfully',
                'enabled': True
            })
            
        except Exception as e:
            logger.error(f"Enable automation error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to enable automation',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='automation/disable')
    def disable_automation(self, request):
        """Disable batch automation"""
        try:
            from django_celery_beat.models import PeriodicTask
            from django.core.cache import cache
            
            # Disable the periodic task
            try:
                periodic_task = PeriodicTask.objects.get(name='recurring-batch-processing')
                periodic_task.enabled = False
                periodic_task.save()
            except PeriodicTask.DoesNotExist:
                pass
            
            # Log activity
            activity_logs = cache.get('batch_automation_logs', [])
            activity_logs.append(f"{timezone.now().strftime('%H:%M:%S')} - Automation disabled by {request.user.username}")
            cache.set('batch_automation_logs', activity_logs[-50:], 86400)  # Keep 50 logs for 24 hours
            
            return Response({
                'success': True,
                'message': 'Batch automation disabled successfully',
                'enabled': False
            })
            
        except Exception as e:
            logger.error(f"Disable automation error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to disable automation',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _generate_batch_recommendations(batch, success_rate, open_rate, click_rate):
    """Generate recommendations based on batch performance"""
    recommendations = []
    
    if success_rate < 80:
        recommendations.append({
            'type': 'warning',
            'title': 'Low Success Rate',
            'message': f'Success rate is {success_rate:.1f}%. Check email configuration and recipient list quality.',
            'action': 'Review SMTP settings and clean recipient list'
        })
    
    if open_rate < 20:
        recommendations.append({
            'type': 'improvement',
            'title': 'Low Open Rate',
            'message': f'Open rate is {open_rate:.1f}%. Consider improving subject lines.',
            'action': 'A/B test subject lines and optimize send timing'
        })
    
    if click_rate < 5:
        recommendations.append({
            'type': 'improvement',
            'title': 'Low Click Rate',
            'message': f'Click rate is {click_rate:.1f}%. Content may need optimization.',
            'action': 'Improve call-to-action and content relevance'
        })
    
    if batch.status == 'completed' and success_rate > 85 and open_rate > 25:
        recommendations.append({
            'type': 'success',
            'title': 'Excellent Performance',
            'message': 'This batch performed exceptionally well!',
            'action': 'Consider duplicating this batch configuration for future campaigns'
        })
    
    return recommendations
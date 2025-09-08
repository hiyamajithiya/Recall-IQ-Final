from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from core.permissions import IsTenantMember
from tenants.models import Tenant
from .models import EmailLog, BatchExecutionEmailLog
from .serializers import (
    EmailLogSerializer, BatchExecutionEmailLogSerializer,
    EmailLogFilterSerializer, EmailLogStatsSerializer
)


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmailLogSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        queryset = EmailLog.objects.select_related(
            'tenant', 'batch', 'batch_recipient', 'documents_received_by'
        )
        
        if self.request.user.role in ['super_admin', 'support_team']:
            # Super admin and support team can see all email logs across all tenants
            pass
        elif self.request.user.tenant:
            queryset = queryset.filter(tenant=self.request.user.tenant)
        else:
            return EmailLog.objects.none()
        
        filter_serializer = EmailLogFilterSerializer(data=self.request.query_params)
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data
            
            if filters.get('email_type'):
                queryset = queryset.filter(email_type=filters['email_type'])
            
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            
            if filters.get('from_email'):
                queryset = queryset.filter(from_email=filters['from_email'])
            
            if filters.get('to_email'):
                queryset = queryset.filter(to_email=filters['to_email'])
            
            if filters.get('date_from'):
                queryset = queryset.filter(created_at__gte=filters['date_from'])
            
            if filters.get('date_to'):
                queryset = queryset.filter(created_at__lte=filters['date_to'])
            
            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(subject__icontains=search_term) |
                    Q(to_email__icontains=search_term) |
                    Q(from_email__icontains=search_term)
                )
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        
        # Debug information
        print(f"Statistics endpoint called by user: {request.user.username} (role: {request.user.role})")
        print(f"Query params: {request.query_params}")
        print(f"Initial queryset count: {queryset.count()}")
        
        # Apply date filtering if provided
        filter_serializer = EmailLogFilterSerializer(data=request.query_params)
        if filter_serializer.is_valid():
            filters = filter_serializer.validated_data
            print(f"Validated filters: {filters}")
            
            if filters.get('date_from'):
                queryset = queryset.filter(created_at__gte=filters['date_from'])
                print(f"After date_from filter: {queryset.count()}")
            
            if filters.get('date_to'):
                # Add one day to include the end date
                end_date = filters['date_to'] + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=end_date)
                print(f"After date_to filter: {queryset.count()}")
        else:
            print(f"Filter validation errors: {filter_serializer.errors}")
        
        total_emails = queryset.count()
        
        # For tenant users, show separate sent and received statistics
        if request.user.role != 'super_admin':
            outgoing_queryset = queryset.filter(direction='outgoing')
            incoming_queryset = queryset.filter(direction='incoming')
            
            sent_emails = outgoing_queryset.filter(status='sent').count()
            failed_emails = outgoing_queryset.filter(status='failed').count()
            pending_emails = outgoing_queryset.filter(status='queued').count()
            received_emails = incoming_queryset.count()
            
            success_rate = (sent_emails / outgoing_queryset.count() * 100) if outgoing_queryset.count() > 0 else 0
            
            by_type = dict(queryset.values('email_type').annotate(count=Count('id')).values_list('email_type', 'count'))
            by_status = dict(queryset.values('status').annotate(count=Count('id')).values_list('status', 'count'))
            by_direction = dict(queryset.values('direction').annotate(count=Count('id')).values_list('direction', 'count'))
            
        else:
            # For super admin, show all statistics normally
            sent_emails = queryset.filter(status='sent').count()
            failed_emails = queryset.filter(status='failed').count()
            pending_emails = queryset.filter(status='queued').count()
            received_emails = 0  # Not applicable for super admin
            
            success_rate = (sent_emails / total_emails * 100) if total_emails > 0 else 0
            
            by_type = dict(queryset.values('email_type').annotate(count=Count('id')).values_list('email_type', 'count'))
            by_status = dict(queryset.values('status').annotate(count=Count('id')).values_list('status', 'count'))
            by_direction = dict(queryset.values('direction').annotate(count=Count('id')).values_list('direction', 'count'))
        
        # Get recent activity from the filtered queryset
        recent_logs = queryset.order_by('-created_at')[:10]
        recent_activity = []
        
        for log in recent_logs:
            recent_activity.append({
                'id': log.id,
                'email_type': log.email_type,
                'status': log.status,
                'direction': log.direction,
                'to_email': log.to_email,
                'subject': log.subject[:50] + '...' if len(log.subject) > 50 else log.subject,
                'created_at': log.created_at
            })
        
        stats = {
            'total_emails': total_emails,
            'sent_emails': sent_emails,
            'received_emails': received_emails,
            'failed_emails': failed_emails,
            'pending_emails': pending_emails,
            'success_rate': round(success_rate, 2),
            'by_type': by_type,
            'by_status': by_status,
            'by_direction': by_direction,
            'recent_activity': recent_activity
        }
        
        print(f"Final stats: total={total_emails}, sent={sent_emails}, received={received_emails}, failed={failed_emails}")
        print(f"by_status: {by_status}")
        print(f"by_type: {by_type}")
        print(f"by_direction: {by_direction}")
        print(f"recent_activity count: {len(recent_activity)}")
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def mark_documents_received(self, request, pk=None):
        """Mark that documents were received for this email log"""
        email_log = self.get_object()
        
        # Only allow marking documents as received for batch emails
        if email_log.email_type != 'batch':
            return Response(
                {'error': 'Documents received can only be marked for batch emails'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        documents_received = request.data.get('documents_received', True)
        
        if documents_received:
            email_log.mark_documents_received(request.user)
            message = 'Documents marked as received'
        else:
            # Allow unmarking documents received
            email_log.documents_received = False
            email_log.documents_received_at = None
            email_log.documents_received_by = None
            email_log.save()
            
            # Update the batch recipient status
            if email_log.batch_recipient:
                email_log.batch_recipient.is_completed = False
                email_log.batch_recipient.documents_received = False
                email_log.batch_recipient.completed_at = None
                email_log.batch_recipient.save()
            
            message = 'Documents unmarked as received'
        
        serializer = self.get_serializer(email_log)
        return Response({
            'message': message,
            'email_log': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_mark_documents_received(self, request):
        """Bulk mark documents received for multiple email logs"""
        email_log_ids = request.data.get('email_log_ids', [])
        documents_received = request.data.get('documents_received', True)
        
        if not email_log_ids:
            return Response(
                {'error': 'email_log_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get email logs that belong to the user's tenant
        queryset = self.get_queryset().filter(
            id__in=email_log_ids,
            email_type='batch'  # Only allow for batch emails
        )
        
        updated_count = 0
        for email_log in queryset:
            if documents_received:
                email_log.mark_documents_received(request.user)
            else:
                email_log.documents_received = False
                email_log.documents_received_at = None
                email_log.documents_received_by = None
                email_log.save()
                
                # Update the batch recipient status
                if email_log.batch_recipient:
                    email_log.batch_recipient.is_completed = False
                    email_log.batch_recipient.documents_received = False
                    email_log.batch_recipient.completed_at = None
                    email_log.batch_recipient.save()
            
            updated_count += 1
        
        return Response({
            'message': f'Updated {updated_count} email logs',
            'updated_count': updated_count
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        import csv
        from django.http import HttpResponse
        
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="email_logs.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Tenant', 'Email Type', 'Status', 'From Email', 'To Email',
            'Subject', 'Error Message', 'Sent At', 'Created At'
        ])
        
        for log in queryset:
            writer.writerow([
                log.id,
                log.tenant.name,
                log.email_type,
                log.status,
                log.from_email,
                log.to_email,
                log.subject,
                log.error_message,
                log.sent_at,
                log.created_at
            ])
        
        return response
    
    @action(detail=False, methods=['get'])
    def daily_stats(self, request):
        days = int(request.query_params.get('days', 30))
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        daily_stats = []
        current_date = start_date
        
        while current_date <= end_date:
            day_logs = queryset.filter(created_at__date=current_date)
            
            daily_stats.append({
                'date': current_date,
                'total': day_logs.count(),
                'sent': day_logs.filter(status='sent').count(),
                'failed': day_logs.filter(status='failed').count(),
                'pending': day_logs.filter(status='queued').count()
            })
            
            current_date += timedelta(days=1)
        
        return Response(daily_stats)
    
    @action(detail=False, methods=['get'])
    def tenant_usage(self, request):
        """Get email usage statistics by tenant for super admin and Support team"""
        if request.user.role not in ['super_admin', 'support_team']:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get current month stats
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get all tenants with their email usage
        tenant_stats = []
        for tenant in Tenant.objects.all():
            # Only count outgoing emails that actually count against limits
            current_month_emails = EmailLog.objects.filter(
                tenant=tenant,
                direction='outgoing',  # Only count emails sent by tenant
                counts_against_limit=True,  # Only count emails that affect limits
                created_at__gte=current_month_start,
                status__in=['sent', 'delivered', 'opened']  # Only count successfully sent emails
            ).count()
            
            # For total stats, also only count outgoing emails
            total_outgoing_emails = EmailLog.objects.filter(
                tenant=tenant, 
                direction='outgoing'
            ).count()
            
            failed_outgoing_emails = EmailLog.objects.filter(
                tenant=tenant, 
                direction='outgoing', 
                status='failed'
            ).count()
            
            # Count incoming emails separately for reference
            total_incoming_emails = EmailLog.objects.filter(
                tenant=tenant, 
                direction='incoming'
            ).count()
            
            usage_percentage = 0
            if tenant.monthly_email_limit > 0:
                usage_percentage = (current_month_emails / tenant.monthly_email_limit) * 100
            
            tenant_stats.append({
                'tenant_id': tenant.id,
                'tenant_name': tenant.name,
                'plan': tenant.plan,
                'status': tenant.status,
                'monthly_limit': tenant.monthly_email_limit,
                'current_month_usage': current_month_emails,
                'usage_percentage': round(usage_percentage, 2),
                'total_emails_sent': total_outgoing_emails,
                'total_emails_received': total_incoming_emails,
                'failed_emails': failed_outgoing_emails,
                'success_rate': round((total_outgoing_emails - failed_outgoing_emails) / total_outgoing_emails * 100, 2) if total_outgoing_emails > 0 else 0
            })
        
        # Sort by usage percentage descending
        tenant_stats.sort(key=lambda x: x['usage_percentage'], reverse=True)
        
        return Response({
            'tenant_statistics': tenant_stats,
            'generated_at': timezone.now()
        })


class BatchExecutionEmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BatchExecutionEmailLogSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        queryset = BatchExecutionEmailLog.objects.select_related('batch', 'email_log__tenant')
        
        if self.request.user.role in ['super_admin', 'support_team']:
            # Super admin and Support team can see all batch execution logs across all tenants
            pass
        elif self.request.user.tenant:
            queryset = queryset.filter(batch__tenant=self.request.user.tenant)
        else:
            return BatchExecutionEmailLog.objects.none()
        
        batch_id = self.request.query_params.get('batch')
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        
        return queryset.order_by('execution_sequence')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_analytics_api(request):
    """Test endpoint to debug analytics data"""
    try:
        from django.db.models import Count
        
        # Basic info
        user_info = {
            'username': request.user.username,
            'role': request.user.role,
            'tenant': request.user.tenant.name if request.user.tenant else None
        }
        
        # Get all logs
        all_logs = EmailLog.objects.all()
        total_count = all_logs.count()
        
        # Get distributions
        status_dist = dict(all_logs.values('status').annotate(count=Count('id')).values_list('status', 'count'))
        type_dist = dict(all_logs.values('email_type').annotate(count=Count('id')).values_list('email_type', 'count'))
        
        # Recent logs
        recent_logs = all_logs.order_by('-created_at')[:5]
        recent_data = []
        for log in recent_logs:
            recent_data.append({
                'id': log.id,
                'status': log.status,
                'email_type': log.email_type,
                'to_email': log.to_email,
                'subject': log.subject[:50],
                'created_at': log.created_at.isoformat()
            })
        
        return Response({
            'user_info': user_info,
            'total_logs': total_count,
            'status_distribution': status_dist,
            'type_distribution': type_dist,
            'recent_logs': recent_data,
            'message': 'Analytics test successful'
        })
        
    except Exception as e:
        import traceback
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
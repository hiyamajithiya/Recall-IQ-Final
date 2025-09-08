from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from core.permissions import IsTenantMember, IsTenantStaff
from .models import EmailLog
from .serializers import EmailLogSerializer, EmailLogFilterSerializer


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for managing email logs with document received functionality"""
    serializer_class = EmailLogSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        queryset = EmailLog.objects.select_related(
            'tenant', 'batch', 'batch_recipient', 'documents_received_by'
        )
        
        if self.request.user.role == 'super_admin':
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
            
            if filters.get('documents_received') is not None:
                queryset = queryset.filter(documents_received=filters['documents_received'])
            
            if filters.get('batch_id'):
                queryset = queryset.filter(batch_id=filters['batch_id'])
            
            search = filters.get('search')
            if search:
                queryset = queryset.filter(
                    Q(subject__icontains=search) |
                    Q(to_email__icontains=search) |
                    Q(from_email__icontains=search)
                )
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_documents_received(self, request, pk=None):
        """Mark an email log as having documents received"""
        email_log = self.get_object()
        
        if email_log.documents_received:
            return Response({
                'error': 'Documents already marked as received'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email_log.mark_documents_received(request.user)
        
        return Response({
            'message': 'Documents marked as received',
            'email_log': EmailLogSerializer(email_log).data
        })
    
    @action(detail=True, methods=['post'])
    def mark_documents_not_received(self, request, pk=None):
        """Mark an email log as not having documents received"""
        email_log = self.get_object()
        
        if not email_log.documents_received:
            return Response({
                'error': 'Documents already marked as not received'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email_log.documents_received = False
        email_log.documents_received_at = None
        email_log.documents_received_by = None
        email_log.save()
        
        if email_log.batch_recipient:
            email_log.batch_recipient.documents_received = False
            email_log.batch_recipient.save()
        
        return Response({
            'message': 'Documents marked as not received',
            'email_log': EmailLogSerializer(email_log).data
        })

    @action(detail=False, methods=['post'])
    def bulk_mark_documents_received(self, request):
        """Mark multiple email logs as having documents received"""
        email_log_ids = request.data.get('email_log_ids', [])
        if not email_log_ids:
            return Response({
                'error': 'Please provide email_log_ids'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter logs that belong to user's tenant and aren't already marked
        email_logs = EmailLog.objects.filter(
            id__in=email_log_ids,
            tenant=request.user.tenant,
            documents_received=False
        )
        
        updated_count = 0
        for log in email_logs:
            log.mark_documents_received(request.user)
            updated_count += 1
        
        return Response({
            'message': f'Marked {updated_count} email logs as documents received',
            'updated_count': updated_count
        })

    @action(detail=False, methods=['post'])
    def bulk_mark_documents_not_received(self, request):
        """Mark multiple email logs as not having documents received"""
        email_log_ids = request.data.get('email_log_ids', [])
        if not email_log_ids:
            return Response({
                'error': 'Please provide email_log_ids'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filter logs that belong to user's tenant and are marked as received
        email_logs = EmailLog.objects.filter(
            id__in=email_log_ids,
            tenant=request.user.tenant,
            documents_received=True
        )
        
        # Update email logs
        updated_count = email_logs.update(
            documents_received=False,
            documents_received_at=None,
            documents_received_by=None
        )
        
        # Update batch recipients
        batch_recipients = set()
        for log in email_logs:
            if log.batch_recipient:
                batch_recipients.add(log.batch_recipient.id)
        
        if batch_recipients:
            from batches.models import BatchRecipient
            BatchRecipient.objects.filter(id__in=batch_recipients).update(
                documents_received=False
            )
        
        return Response({
            'message': f'Marked {updated_count} email logs as documents not received',
            'updated_count': updated_count
        })

"""
API endpoint for processing scheduled batches
This allows frontend to trigger batch processing
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from batches.models import Batch, BatchRecipient
from batches.tasks import execute_batch_subcycle
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_scheduled_batches(request):
    """
    Process all scheduled batches that are due for execution
    """
    try:
        current_time = timezone.now()
        
        # Get scheduled batches that are due
        due_batches = Batch.objects.filter(
            status='scheduled',
            start_time__lte=current_time,
            tenant=request.user.tenant
        )
        
        if not due_batches.exists():
            return Response({
                'success': True,
                'message': 'No batches due for execution',
                'processed': 0,
                'failed': 0
            })
        
        processed_count = 0
        failed_count = 0
        results = []
        
        for batch in due_batches:
            try:
                # Fix recipients without next_email_due_at
                fix_recipients_for_batch(batch)
                
                # Execute the batch
                execute_batch_subcycle(batch.id)
                
                # Check results
                batch.refresh_from_db()
                
                processed_count += 1
                results.append({
                    'batch_id': batch.id,
                    'batch_name': batch.name,
                    'status': 'success',
                    'emails_sent': batch.emails_sent,
                    'emails_failed': batch.emails_failed
                })
                
            except Exception as e:
                failed_count += 1
                results.append({
                    'batch_id': batch.id,
                    'batch_name': batch.name,
                    'status': 'error',
                    'error': str(e)
                })
                logger.error(f"Error processing batch {batch.id}: {e}")
        
        return Response({
            'success': True,
            'message': f'Processed {processed_count} batches successfully, {failed_count} failed',
            'processed': processed_count,
            'failed': failed_count,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in process_scheduled_batches API: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_specific_batch(request, batch_id):
    """
    Process a specific batch immediately
    """
    try:
        batch = Batch.objects.get(
            id=batch_id,
            tenant=request.user.tenant
        )
        
        # Fix recipients without next_email_due_at
        fix_recipients_for_batch(batch)
        
        # Execute the batch
        execute_batch_subcycle(batch_id)
        
        # Check results
        batch.refresh_from_db()
        
        return Response({
            'success': True,
            'message': f'Batch {batch.name} processed successfully',
            'batch_id': batch.id,
            'batch_name': batch.name,
            'emails_sent': batch.emails_sent,
            'emails_failed': batch.emails_failed,
            'status': batch.status
        })
        
    except Batch.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Batch {batch_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error processing batch {batch_id}: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fix_batch_recipients(request):
    """
    Fix all batch recipients with missing next_email_due_at
    """
    try:
        # Find recipients without next_email_due_at
        broken_recipients = BatchRecipient.objects.filter(
            next_email_due_at__isnull=True,
            batch__status__in=['scheduled', 'running'],
            batch__tenant=request.user.tenant,
            is_completed=False
        )
        
        fixed_count = 0
        for recipient in broken_recipients:
            recipient.next_email_due_at = recipient.batch.start_time
            recipient.save()
            fixed_count += 1
        
        return Response({
            'success': True,
            'message': f'Fixed {fixed_count} recipients',
            'fixed_count': fixed_count
        })
        
    except Exception as e:
        logger.error(f"Error fixing recipients: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def fix_recipients_for_batch(batch):
    """
    Helper function to fix recipients for a specific batch
    """
    recipients_without_due_time = BatchRecipient.objects.filter(
        batch=batch,
        next_email_due_at__isnull=True,
        is_completed=False
    )
    
    if recipients_without_due_time.exists():
        recipients_without_due_time.update(next_email_due_at=batch.start_time)
        logger.info(f"Fixed {recipients_without_due_time.count()} recipients for batch {batch.id}")

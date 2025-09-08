"""
Batch model signals for cache invalidation and automation triggers
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Batch
from core.cache_utils import invalidate_tenant_cache
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Batch)
def invalidate_cache_on_batch_save(sender, instance, created, **kwargs):
    """Invalidate dashboard cache when batches change"""
    if instance.tenant_id:
        invalidate_tenant_cache(instance.tenant_id)
        logger.debug(f"Invalidated cache for tenant {instance.tenant_id} due to Batch update")


@receiver(post_save, sender=Batch)
def trigger_batch_automation(sender, instance, created, **kwargs):
    """
    Trigger batch automation when a batch is created or updated
    Enhanced with multi-tenant email configuration validation
    """
    from django.conf import settings
    
    try:
        # Only process if batch is ready for automation
        if instance.status not in ['pending', 'scheduled']:
            return
        
        # Check if tenant has email configuration
        from core.models import UserEmailConfiguration
        email_config = UserEmailConfiguration.objects.filter(
            user__tenant=instance.tenant,
            is_active=True
        ).first()
        
        if not email_config:
            # Fallback: try to find default config for any user in tenant
            email_config = UserEmailConfiguration.objects.filter(
                user__tenant=instance.tenant,
                is_default=True
            ).first()
        
        if not email_config:
            logger.warning(f"Batch {instance.id} cannot be automated - no email configuration for users in tenant {instance.tenant.name}")
            instance.status = 'failed'
            instance.error_message = f"No active email configuration found for users in tenant {instance.tenant.name}"
            instance.save()
            return
        
        # Assign the email configuration to the batch for legacy system compatibility
        if not instance.email_configuration:
            instance.email_configuration = email_config
            instance.save(update_fields=['email_configuration'])
        
        # Validate email configuration
        from core.email_service import MultiTenantEmailService
        
        try:
            is_valid, validation_message = MultiTenantEmailService.validate_configuration(email_config)
            if not is_valid:
                logger.error(f"Batch {instance.id} cannot be automated - invalid email configuration: {validation_message}")
                instance.status = 'failed'
                instance.error_message = f"Email configuration invalid: {validation_message}"
                instance.save()
                return
        except Exception as e:
            logger.error(f"Error validating email configuration for batch {instance.id}: {str(e)}")
            instance.status = 'failed'
            instance.error_message = f"Email configuration validation error: {str(e)}"
            instance.save()
            return
        
        # If this is a new batch or status changed to scheduled
        if (created and instance.status == 'scheduled') or (not created and instance.status == 'scheduled'):
            logger.info(f"Batch automation triggered for batch {instance.id} '{instance.name}' using {email_config.provider}")
            
            # Check if the batch should run immediately
            now = timezone.now()
            should_process_immediately = False
            
            if instance.start_time and instance.start_time <= now:
                should_process_immediately = True
                logger.info(f"Batch {instance.id} is overdue (start_time: {instance.start_time}, now: {now})")
            
            # Development mode - process immediately for testing
            if settings.DEBUG:
                should_process_immediately = True
                logger.info(f"Development mode: Processing batch {instance.id} immediately")
            
            # Determine which task system to use
            try:
                # Temporarily disabled multi-tenant tasks - using legacy system
                raise ImportError("Multi-tenant tasks temporarily disabled")
                
                # Try to use the new multi-tenant task
                from .tasks_multitenant import process_batch_emails_multitenant
                
                if should_process_immediately:
                    logger.info(f"Starting immediate multi-tenant processing for batch {instance.id}")
                    process_batch_emails_multitenant.delay(instance.id)
                else:
                    logger.info(f"Scheduling multi-tenant batch {instance.id} for {instance.start_time}")
                    if instance.start_time:
                        process_batch_emails_multitenant.apply_async(args=[instance.id], eta=instance.start_time)
                        
            except ImportError:
                # Fall back to legacy system
                logger.info(f"Multi-tenant tasks not available, using legacy system for batch {instance.id}")
                from .tasks import schedule_recurring_batches, update_batch_statuses
                
                if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                    # Development mode - call tasks directly
                    logger.info(f"Development mode: Running legacy tasks directly")
                    update_batch_statuses()
                    schedule_recurring_batches()
                else:
                    # Production mode - use Celery queue
                    update_batch_statuses.delay()
                    schedule_recurring_batches.delay()
                
                logger.info(f"Legacy batch automation triggered for batch {instance.id}")
                
    except Exception as e:
        logger.error(f"Error in batch automation trigger: {str(e)}")
        # Mark batch as failed if automation setup fails
        try:
            instance.status = 'failed'
            instance.error_message = f"Automation setup error: {str(e)}"
            instance.save()
        except:
            pass


@receiver(post_delete, sender=Batch)
def invalidate_cache_on_batch_delete(sender, instance, **kwargs):
    """Invalidate dashboard cache when batches are deleted"""
    if instance.tenant_id:
        invalidate_tenant_cache(instance.tenant_id)
        logger.debug(f"Invalidated cache for tenant {instance.tenant_id} due to Batch deletion")
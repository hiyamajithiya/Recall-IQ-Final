"""
EmailLog model signals for cache invalidation
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import EmailLog
from core.cache_utils import invalidate_tenant_cache
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=EmailLog)
def invalidate_cache_on_email_log_save(sender, instance, created, **kwargs):
    """Invalidate dashboard cache when email logs change"""
    if instance.tenant_id:
        invalidate_tenant_cache(instance.tenant_id)
        logger.debug(f"Invalidated cache for tenant {instance.tenant_id} due to EmailLog update")


@receiver(post_delete, sender=EmailLog)
def invalidate_cache_on_email_log_delete(sender, instance, **kwargs):
    """Invalidate dashboard cache when email logs are deleted"""
    if instance.tenant_id:
        invalidate_tenant_cache(instance.tenant_id)
        logger.debug(f"Invalidated cache for tenant {instance.tenant_id} due to EmailLog deletion")
"""
Tenant model signals for automatic notification sending

This module contains Django signals that automatically trigger email notifications
when tenant account details are modified by super admin.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Tenant
from core.tenant_notifications import (
    notify_plan_change,
    notify_status_change, 
    notify_email_limit_change,
    notify_generic_update
)
from core.cache_utils import invalidate_tenant_cache, invalidate_dashboard_cache
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

# Store original values before save
_tenant_original_values = {}


@receiver(pre_save, sender=Tenant)
def store_original_tenant_values(sender, instance, **kwargs):
    """Store original values before save to detect changes"""
    global _tenant_original_values
    
    if instance.pk:
        try:
            original = Tenant.objects.get(pk=instance.pk)
            _tenant_original_values[instance.pk] = {
                'plan': original.plan,
                'status': original.status,
                'monthly_email_limit': original.monthly_email_limit,
                'subscription_start_date': original.subscription_start_date,
                'subscription_end_date': original.subscription_end_date,
                'trial_end_date': original.trial_end_date,
                'contact_email': original.contact_email,
                'billing_email': original.billing_email,
                'is_active': original.is_active,
            }
        except Tenant.DoesNotExist:
            _tenant_original_values[instance.pk] = {}
    else:
        _tenant_original_values[instance.pk] = {}


@receiver(post_save, sender=Tenant)
def send_tenant_change_notifications(sender, instance, created, **kwargs):
    """Send notifications when tenant details are changed"""
    global _tenant_original_values
    
    # Skip notifications for new tenant creation (handled by user creation welcome email)
    if created:
        _tenant_original_values.pop(instance.pk, None)
        return
    
    try:
        # Get the user who made the changes (if available in request context)
        changed_by = getattr(instance, '_changed_by', None)
        logger.info(f"🔍 Signal triggered for tenant {instance.name}, changed_by: {changed_by}")
        
        if not changed_by:
            # Fallback to super admin if no specific user found
            changed_by = User.objects.filter(role='super_admin').first()
            logger.info(f"🔄 Using fallback super admin: {changed_by}")
        
        # Get original values
        original_values = _tenant_original_values.get(instance.pk, {})
        
        # Detect and handle specific changes
        changes_detected = {}
        notification_sent = False
        
        # Plan change notification
        if original_values.get('plan') and original_values['plan'] != instance.plan:
            logger.info(f"Plan changed for tenant {instance.name}: {original_values['plan']} -> {instance.plan}")
            notify_plan_change(instance, original_values['plan'], instance.plan, changed_by)
            changes_detected['plan'] = {'old': original_values['plan'], 'new': instance.plan}
            notification_sent = True
        
        # Status change notification
        if original_values.get('status') and original_values['status'] != instance.status:
            logger.info(f"Status changed for tenant {instance.name}: {original_values['status']} -> {instance.status}")
            notify_status_change(instance, original_values['status'], instance.status, changed_by)
            changes_detected['status'] = {'old': original_values['status'], 'new': instance.status}
            notification_sent = True
        
        # Email limit change notification
        if (original_values.get('monthly_email_limit') is not None and 
            original_values['monthly_email_limit'] != instance.monthly_email_limit):
            logger.info(f"Email limit changed for tenant {instance.name}: {original_values['monthly_email_limit']} -> {instance.monthly_email_limit}")
            notify_email_limit_change(instance, original_values['monthly_email_limit'], instance.monthly_email_limit, changed_by)
            changes_detected['monthly_email_limit'] = {
                'old': original_values['monthly_email_limit'], 
                'new': instance.monthly_email_limit
            }
            notification_sent = True
        
        # Check for other significant changes
        other_changes = {}
        significant_fields = ['contact_email', 'billing_email', 'subscription_start_date', 'subscription_end_date', 'trial_end_date']
        
        for field in significant_fields:
            old_value = original_values.get(field)
            new_value = getattr(instance, field)
            if old_value != new_value and old_value is not None:
                other_changes[field] = {'old': old_value, 'new': new_value}
        
        # Send generic notification for other changes (if no specific notification sent)
        if other_changes and not notification_sent:
            logger.info(f"Generic changes detected for tenant {instance.name}: {other_changes}")
            notify_generic_update(instance, other_changes, changed_by)
            notification_sent = True
        
        # Log if changes were made but no notification sent
        if changes_detected and not notification_sent:
            logger.info(f"Changes detected for tenant {instance.name} but no notification sent: {changes_detected}")
        
    except Exception as e:
        logger.error(f"Error sending tenant change notification: {e}")
    finally:
        # Invalidate dashboard cache since tenant data changed
        invalidate_tenant_cache(instance.id)
        
        # Clean up stored values
        _tenant_original_values.pop(instance.pk, None)


def manual_notify_trial_expiry(tenant_id, admin_user=None):
    """Manually trigger trial expiry notification"""
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        from core.tenant_notifications import notify_trial_expiry
        return notify_trial_expiry(tenant, admin_user)
    except Tenant.DoesNotExist:
        logger.error(f"Tenant with ID {tenant_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending manual trial expiry notification: {e}")
        return False


def manual_notify_subscription_renewal(tenant_id, admin_user=None):
    """Manually trigger subscription renewal notification"""
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        from core.tenant_notifications import notify_subscription_renewal
        return notify_subscription_renewal(tenant, admin_user)
    except Tenant.DoesNotExist:
        logger.error(f"Tenant with ID {tenant_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending manual subscription renewal notification: {e}")
        return False
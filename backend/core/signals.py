"""
User model signals for automatic notification sending

This module contains Django signals that automatically trigger email notifications
when user/staff account details are modified by super admin or tenant admin.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from core.tenant_notifications import notify_generic_update
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

# Store original values before save
_user_original_values = {}


@receiver(pre_save, sender=User)
def store_original_user_values(sender, instance, **kwargs):
    """Store original values before save to detect changes"""
    global _user_original_values
    
    if instance.pk:
        try:
            original = User.objects.get(pk=instance.pk)
            _user_original_values[instance.pk] = {
                'username': original.username,
                'email': original.email,
                'first_name': original.first_name,
                'last_name': original.last_name,
                'role': original.role,
                'tenant': original.tenant,
                'is_active': original.is_active,
            }
        except User.DoesNotExist:
            _user_original_values[instance.pk] = {}
    else:
        _user_original_values[instance.pk] = {}


@receiver(post_save, sender=User)
def send_user_change_notifications(sender, instance, created, **kwargs):
    """Send notifications when user/staff details are changed"""
    global _user_original_values
    
    # Skip notifications for new user creation (handled by welcome email)
    if created:
        _user_original_values.pop(instance.pk, None)
        return
    
    # Skip notifications for self-updates (users updating their own profile)
    changed_by = getattr(instance, '_changed_by', None)
    if changed_by and changed_by.id == instance.id:
        logger.info(f"Skipping notification for self-update by user {instance.username}")
        _user_original_values.pop(instance.pk, None)
        return
    
    # Only send notifications if the user belongs to a tenant
    if not instance.tenant:
        logger.info(f"Skipping notification for user {instance.username} - no tenant assigned")
        _user_original_values.pop(instance.pk, None)
        return
    
    try:
        logger.info(f"🔍 User signal triggered for {instance.username}, changed_by: {changed_by}")
        
        if not changed_by:
            # Fallback to super admin if no specific user found
            changed_by = User.objects.filter(role='super_admin').first()
            logger.info(f"🔄 Using fallback super admin: {changed_by}")
        
        # Get original values
        original_values = _user_original_values.get(instance.pk, {})
        
        # Detect changes
        changes_detected = {}
        significant_fields = ['username', 'email', 'first_name', 'last_name', 'role', 'tenant', 'is_active']
        
        for field in significant_fields:
            old_value = original_values.get(field)
            new_value = getattr(instance, field)
            
            # Special handling for tenant field (compare IDs)
            if field == 'tenant':
                old_tenant_id = old_value.id if old_value else None
                new_tenant_id = new_value.id if new_value else None
                if old_tenant_id != new_tenant_id:
                    changes_detected[field] = {
                        'old': old_value.name if old_value else 'No Tenant',
                        'new': new_value.name if new_value else 'No Tenant'
                    }
            elif old_value != new_value and old_value is not None:
                # Format role display nicely
                if field == 'role':
                    old_display = dict(User.ROLE_CHOICES).get(old_value, old_value)
                    new_display = dict(User.ROLE_CHOICES).get(new_value, new_value)
                    changes_detected[field] = {'old': old_display, 'new': new_display}
                else:
                    changes_detected[field] = {'old': old_value, 'new': new_value}
        
        # Send notification if significant changes were made
        if changes_detected:
            logger.info(f"Significant changes detected for user {instance.username}: {changes_detected}")
            
            # Determine the correct tenant to notify
            tenant_to_notify = instance.tenant
            if not tenant_to_notify and 'tenant' in changes_detected:
                # If user was moved to a different tenant, notify the new tenant
                tenant_to_notify = new_value if field == 'tenant' and new_value else None
            
            if tenant_to_notify:
                # Format the notification message
                user_type = 'Staff Member' if instance.role == 'staff' else f'{instance.get_role_display()}'
                notification_changes = {
                    'user_update': {
                        'old': f"Previous {user_type} Details",
                        'new': f"Updated {user_type} Details"
                    },
                    'updated_user_id': instance.id,
                    'updated_user_name': f"{instance.first_name} {instance.last_name}".strip() or instance.username,
                    'updated_user_email': instance.email,
                    'updated_user_role': instance.get_role_display(),
                    'changes': changes_detected
                }
                
                result = notify_generic_update(tenant_to_notify, notification_changes, changed_by)
                if result:
                    logger.info(f"Successfully sent user update notification for {instance.username} to tenant {tenant_to_notify.name}")
                else:
                    logger.error(f"Failed to send user update notification for {instance.username} to tenant {tenant_to_notify.name}")
            else:
                logger.warning(f"No tenant found to notify for user {instance.username} changes")
        else:
            logger.info(f"No significant changes detected for user {instance.username}")
        
    except Exception as e:
        logger.error(f"Error sending user change notification: {e}")
    finally:
        # Clean up stored values
        _user_original_values.pop(instance.pk, None)
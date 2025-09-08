"""
Tenant Notification System

This module handles email notifications for tenant account changes made by super admin.
It includes various notification types like plan changes, trial expiry, status updates, etc.
"""

from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from logs.models import EmailLog
from .models import UserEmailConfiguration
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def get_super_admin_email_config():
    """Get super admin's default email configuration for sending notifications"""
    try:
        super_admin = User.objects.filter(role='super_admin').first()
        if super_admin:
            email_config = UserEmailConfiguration.objects.filter(
                user=super_admin, 
                is_default=True, 
                is_active=True
            ).first()
            return email_config
    except Exception as e:
        logger.error(f"Error getting super admin email config: {e}")
    return None


def setup_email_backend():
    """Setup email backend using super admin configuration or Django settings"""
    backend = None
    from_email = settings.DEFAULT_FROM_EMAIL
    config_source = "Django Settings"
    
    try:
        email_config = get_super_admin_email_config()
        if email_config:
            password = email_config.decrypt_password()
            if password and password.strip():
                backend = EmailBackend(
                    host=email_config.email_host,
                    port=int(email_config.email_port),
                    username=email_config.email_host_user,
                    password=password,
                    use_tls=email_config.email_use_tls,
                    use_ssl=email_config.email_use_ssl,
                    fail_silently=False
                )
                from_email = email_config.from_email
                config_source = f"Super Admin Config: {email_config.name}"
    except Exception as e:
        logger.error(f"Error setting up email backend: {e}")
    
    # Fallback to console backend if no proper configuration
    if not backend and not (settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD):
        from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
        backend = ConsoleEmailBackend()
        config_source += " - CONSOLE BACKEND"
    
    return backend, from_email, config_source


def send_tenant_notification(tenant, notification_type, changes=None, changed_by=None):
    """
    Send notification email to tenant about account changes
    
    Args:
        tenant: Tenant instance
        notification_type: Type of notification (plan_change, trial_expiry, etc.)
        changes: Dictionary of field changes (old_value -> new_value)
        changed_by: User who made the changes
    """
    try:
        # Get tenant admin users to notify
        tenant_users = User.objects.filter(
            tenant=tenant,
            role__in=['tenant_admin', 'staff'],
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        if not tenant_users.exists():
            logger.warning(f"No tenant users found to notify for tenant: {tenant.name}")
            return False
        
        # Setup email configuration
        backend, from_email, config_source = setup_email_backend()
        
        # Generate email content based on notification type
        subject, body = generate_notification_content(tenant, notification_type, changes, changed_by)
        
        success_count = 0
        for user in tenant_users:
            try:
                # Create email log entry
                email_log = EmailLog.objects.create(
                    tenant=tenant,
                    email_type='notification',
                    status='queued',
                    direction='incoming',  # Notifications from super admin are incoming to tenant
                    from_email=from_email,
                    to_email=user.email,
                    subject=subject,
                    body=body,
                    sent_by_user=changed_by,  # Track who triggered the notification
                    counts_against_limit=False,  # Admin notifications don't count against tenant limits
                    metadata={
                        'notification_type': notification_type,
                        'tenant_id': tenant.id,
                        'tenant_name': tenant.name,
                        'user_id': user.id,
                        'user_role': user.role,
                        'changed_by_id': changed_by.id if changed_by else None,
                        'changed_by_name': changed_by.get_full_name() or changed_by.username if changed_by else 'System',
                        'changes': changes or {},
                        'config_source': config_source
                    }
                )
                
                # Create and send email
                notification_email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=from_email,
                    to=[user.email],
                    connection=backend
                )
                
                result = notification_email.send()
                if result == 1:
                    email_log.status = 'sent'
                    email_log.sent_at = timezone.now()
                    success_count += 1
                    logger.info(f"Notification sent to {user.email} for tenant {tenant.name}")
                else:
                    email_log.status = 'failed'
                    email_log.error_message = "Email send returned 0"
                    logger.error(f"Failed to send notification to {user.email}")
                
                email_log.save()
                
            except Exception as e:
                logger.error(f"Error sending notification to {user.email}: {e}")
                if 'email_log' in locals():
                    email_log.status = 'failed'
                    email_log.error_message = str(e)
                    email_log.save()
        
        logger.info(f"Sent {success_count}/{tenant_users.count()} notifications for tenant {tenant.name}")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error in send_tenant_notification: {e}")
        return False


def generate_notification_content(tenant, notification_type, changes, changed_by):
    """Generate email subject and body based on notification type"""
    
    company_name = tenant.name
    admin_name = changed_by.get_full_name() or changed_by.username if changed_by else 'RecallIQ Administrator'
    current_date = timezone.now().strftime('%B %d, %Y')
    
    if notification_type == 'plan_change':
        old_plan = changes.get('plan', {}).get('old', 'Unknown')
        new_plan = changes.get('plan', {}).get('new', 'Unknown')
        
        subject = f"Plan Update: Your {company_name} RecallIQ Plan Has Been Changed"
        body = f"""Dear {company_name} Team,

ACCOUNT PLAN UPDATE

Your RecallIQ account plan has been updated by our administrator.

PLAN CHANGE DETAILS:

Previous Plan: {old_plan.replace('_', ' ').title()}
New Plan: {new_plan.replace('_', ' ').title()}
Effective Date: {current_date}
Updated By: {admin_name}

NEW PLAN FEATURES:

{get_plan_features(new_plan)}

EMAIL LIMITS AND USAGE:
- Monthly Email Limit: {tenant.monthly_email_limit:,} emails
- Current Usage This Month: {tenant.emails_sent_this_month_countable:,} emails
- Remaining Emails: {max(0, tenant.monthly_email_limit - tenant.emails_sent_this_month_countable):,} emails

WHAT THIS MEANS FOR YOU:

+ All existing features remain available
+ New plan benefits are now active
+ Email limits have been updated accordingly
+ No action required from your side

NEXT STEPS:

1. Log into your RecallIQ dashboard to see updated features
2. Review your new email limits and plan benefits
3. Contact support if you have any questions

Access your account: {settings.FRONTEND_URL or 'http://localhost:3000'}

NEED ASSISTANCE?

If you have questions about your plan change:
Email: {settings.SUPPORT_EMAIL or 'support@recalliq.com'}
Support: Available in your dashboard
Documentation: {settings.FRONTEND_URL or 'http://localhost:3000'}/help

Thank you for using RecallIQ!

Best regards,
{admin_name}
RecallIQ Administrator

---
This notification was sent because your account plan was updated.
For support: {settings.SUPPORT_EMAIL or 'support@recalliq.com'}
(C) {timezone.now().year} RecallIQ. All rights reserved."""

    elif notification_type == 'trial_expiry':
        days_remaining = tenant.days_until_expiry
        
        subject = f"Trial Expiry Notice: Your {company_name} Trial {'Expires Soon' if days_remaining > 0 else 'Has Expired'}"
        body = f"""Dear {company_name} Team,

{'TRIAL EXPIRY REMINDER' if days_remaining > 0 else 'TRIAL EXPIRED'}

{'Your RecallIQ trial period is ending soon.' if days_remaining > 0 else 'Your RecallIQ trial period has expired.'}

TRIAL STATUS:

Trial Status: {'Expiring Soon' if days_remaining > 0 else 'Expired'}
{f'Days Remaining: {days_remaining} days' if days_remaining > 0 else 'Expired On: ' + (tenant.trial_end_date.strftime('%B %d, %Y') if tenant.trial_end_date else 'N/A')}
Current Plan: {tenant.get_plan_display()}
Account Status: {tenant.get_status_display()}

YOUR TRIAL USAGE:
- Emails Sent: {tenant.emails_sent_this_month_countable:,} / {tenant.monthly_email_limit:,}
- Usage: {tenant.email_usage_percentage:.1f}%

CONTINUE YOUR RECALLIQ JOURNEY:

To maintain uninterrupted access to your email management platform:

1. Choose a subscription plan that fits your needs
2. Upgrade before your trial expires
3. Contact our sales team for assistance

Available Plans:
- Starter Plan: Perfect for small teams
- Professional Plan: Advanced features for growing businesses  
- Enterprise Plan: Full-scale solution for large organizations
- Custom Plan: Tailored to your specific requirements

UPGRADE NOW:

Access your account: {settings.FRONTEND_URL or 'http://localhost:3000'}
Go to: Account Settings -> Billing & Plans

{'WHAT HAPPENS NEXT:' if days_remaining > 0 else 'ACCOUNT STATUS:'}

{f'''Your account will remain active for {days_remaining} more days.
After trial expiry, some features may be limited until you upgrade.''' if days_remaining > 0 else '''Your account access may be limited.
Please contact our team to reactivate your account with a paid plan.'''}

NEED HELP CHOOSING A PLAN?

Our team is here to help you select the perfect plan:
Email: {settings.SUPPORT_EMAIL or 'support@recalliq.com'}
Sales: Contact through your dashboard
Live Chat: Available 24/7

Don't lose access to your valuable email campaigns and data!

Best regards,
{admin_name}
RecallIQ Team

---
This is an automated trial expiry notification.
For immediate assistance: {settings.SUPPORT_EMAIL or 'support@recalliq.com'}
(C) {timezone.now().year} RecallIQ. All rights reserved."""

    elif notification_type == 'status_change':
        old_status = changes.get('status', {}).get('old', 'Unknown')
        new_status = changes.get('status', {}).get('new', 'Unknown')
        
        subject = f" Account Status Update: Your {company_name} Account is Now {new_status.title()}"
        body = f"""Dear {company_name} Team,

 ACCOUNT STATUS UPDATE

Your RecallIQ account status has been updated by our administrator.

================================================================
                        STATUS CHANGE DETAILS
================================================================

Previous Status: {old_status.replace('_', ' ').title()}
New Status: {new_status.replace('_', ' ').title()}
Effective Date: {current_date}
Updated By: {admin_name}

 ACCOUNT INFORMATION:
- Company: {company_name}
- Plan: {tenant.get_plan_display()}
- Contact: {tenant.contact_email}
- Monthly Email Limit: {tenant.monthly_email_limit:,} emails

{get_status_implications(new_status)}

 ACCESS YOUR ACCOUNT:

Dashboard: {settings.FRONTEND_URL or 'http://localhost:3000'}
Support: {settings.SUPPORT_EMAIL or 'support@recalliq.com'}

If you have questions about this status change, please contact our support team.

Best regards,
{admin_name}
RecallIQ Administrator

---
This notification was sent because your account status was updated.
(C) {timezone.now().year} RecallIQ. All rights reserved."""

    elif notification_type == 'email_limit_change':
        old_limit = changes.get('monthly_email_limit', {}).get('old', 0)
        new_limit = changes.get('monthly_email_limit', {}).get('new', 0)
        
        subject = f"Email Limit Updated: Your {company_name} Monthly Limit Changed"
        body = f"""Dear {company_name} Team,

EMAIL LIMIT UPDATE

Your monthly email limit has been updated by our administrator.

================================================================
                        LIMIT CHANGE DETAILS
================================================================

Previous Limit: {old_limit:,} emails per month
New Limit: {new_limit:,} emails per month
Change: {'+' if new_limit > old_limit else ''}{new_limit - old_limit:,} emails
Effective Date: {current_date}
Updated By: {admin_name}

CURRENT USAGE:
- Emails Sent This Month: {tenant.emails_sent_this_month_countable:,}
- New Monthly Limit: {new_limit:,}
- Remaining Emails: {max(0, new_limit - tenant.emails_sent_this_month_countable):,}
- Usage Percentage: {min(100, (tenant.emails_sent_this_month_countable / new_limit * 100) if new_limit > 0 else 0):.1f}%

{'INCREASED CAPACITY:' if new_limit > old_limit else 'REDUCED CAPACITY:'}

{f'Great news! Your email capacity has been increased by {new_limit - old_limit:,} emails per month.' if new_limit > old_limit else f'Please note that your email limit has been reduced by {old_limit - new_limit:,} emails per month.'}

OPTIMIZATION TIPS:

- Monitor your email usage in the dashboard
- Set up usage alerts to track consumption
- Plan your email campaigns according to your limits
- Contact support if you need limit adjustments

Access your dashboard: {settings.FRONTEND_URL or 'http://localhost:3000'}

Best regards,
{admin_name}
RecallIQ Administrator

---
Monitor your email usage to stay within limits.
(C) {timezone.now().year} RecallIQ. All rights reserved."""

    elif notification_type == 'subscription_renewal':
        subject = f" Subscription Renewed: Your {company_name} RecallIQ Subscription"
        body = f"""Dear {company_name} Team,

 SUBSCRIPTION RENEWAL

Your RecallIQ subscription has been successfully renewed!

================================================================
                        RENEWAL DETAILS
================================================================

Plan: {tenant.get_plan_display()}
Status: {tenant.get_status_display()}
Renewal Date: {current_date}
{f'Next Renewal: {tenant.subscription_end_date.strftime("%B %d, %Y")}' if tenant.subscription_end_date else ''}
Processed By: {admin_name}

 WHAT'S INCLUDED:

{get_plan_features(tenant.plan)}

 EMAIL ALLOCATION:
- Monthly Limit: {tenant.monthly_email_limit:,} emails
- Current Usage: {tenant.emails_sent_this_month_countable:,} emails
- Available: {max(0, tenant.monthly_email_limit - tenant.emails_sent_this_month_countable):,} emails

 CONTINUE BUILDING GREAT EMAIL CAMPAIGNS:

Your subscription renewal ensures uninterrupted access to all RecallIQ features.
Log in to your dashboard to continue managing your email campaigns.

Access your account: {settings.FRONTEND_URL or 'http://localhost:3000'}

Thank you for continuing with RecallIQ!

Best regards,
{admin_name}
RecallIQ Team

---
Your subscription has been renewed successfully.
(C) {timezone.now().year} RecallIQ. All rights reserved."""

    else:  # generic_update
        subject = f" Account Update: Changes Made to Your {company_name} RecallIQ Account"
        body = f"""Dear {company_name} Team,

 ACCOUNT UPDATE NOTIFICATION

Your RecallIQ account has been updated by our administrator.

================================================================
                        UPDATE DETAILS
================================================================

Updated Date: {current_date}
Updated By: {admin_name}

Changes Made:
{format_changes(changes) if changes else 'Account information has been updated.'}

 CURRENT ACCOUNT STATUS:
- Company: {company_name}
- Plan: {tenant.get_plan_display()}
- Status: {tenant.get_status_display()}
- Monthly Email Limit: {tenant.monthly_email_limit:,} emails

 REVIEW YOUR ACCOUNT:

Please log in to your dashboard to review the changes:
{settings.FRONTEND_URL or 'http://localhost:3000'}

If you have questions about these updates, please contact our support team.

Best regards,
{admin_name}
RecallIQ Administrator

---
This notification was sent because your account was updated.
(C) {timezone.now().year} RecallIQ. All rights reserved."""
    
    return subject, body


def get_plan_features(plan):
    """Get feature list for a specific plan"""
    features = {
        'starter': """- 1,000 emails per month
- Basic email templates
- Contact management
- Email delivery tracking
- Standard support""",
        'professional': """- 10,000 emails per month
- Advanced email templates
- Contact groups & segmentation
- Advanced analytics & reporting
- A/B testing capabilities
- Priority support""",
        'enterprise': """- 50,000+ emails per month
- Custom email templates
- Advanced automation
- Detailed analytics & insights
- API access
- White-label options
- Dedicated support""",
        'custom': """- Customized email limits
- Tailored features
- Enterprise integrations
- Custom reporting
- Dedicated account manager
- 24/7 premium support"""
    }
    return features.get(plan, "- Custom plan features as agreed")


def get_status_implications(status):
    """Get implications text for different status changes"""
    implications = {
        'active': """ACCOUNT ACTIVE:
- Full access to all features
- Email sending enabled
- All services operational""",
        'trial': """TRIAL MODE:
- Limited time access
- All features available during trial
- Upgrade required before expiry""",
        'suspended': """ACCOUNT SUSPENDED:
- Limited access to features
- Email sending may be restricted
- Contact support for reactivation""",
        'cancelled': """ACCOUNT CANCELLED:
- Services will be discontinued
- Data retention as per policy
- Contact support to reactivate""",
        'expired': """ACCOUNT EXPIRED:
- Subscription has ended
- Limited access to features
- Renewal required for full access"""
    }
    return implications.get(status, "- Account status updated")


def format_changes(changes):
    """Format changes dictionary into readable text"""
    if not changes:
        return "General account updates"
    
    formatted = []
    
    # Special handling for user updates
    if 'user_update' in changes:
        user_name = changes.get('updated_user_name', 'Staff Member')
        user_email = changes.get('updated_user_email', '')
        user_role = changes.get('updated_user_role', 'Staff')
        
        formatted.append(f"STAFF MEMBER UPDATED: {user_name}")
        if user_email:
            formatted.append(f"   Email: {user_email}")
        formatted.append(f"   Role: {user_role}")
        formatted.append("")
        
        # Format the actual field changes
        user_changes = changes.get('changes', {})
        if user_changes:
            formatted.append("CHANGES MADE:")
            for field, change in user_changes.items():
                if isinstance(change, dict) and 'old' in change and 'new' in change:
                    field_name = field.replace('_', ' ').title()
                    old_val = str(change['old'])
                    new_val = str(change['new'])
                    formatted.append(f"   - {field_name}: {old_val} -> {new_val}")
        
        return '\n'.join(formatted)
    
    # Standard formatting for other changes
    for field, change in changes.items():
        if isinstance(change, dict) and 'old' in change and 'new' in change:
            field_name = field.replace('_', ' ').title()
            old_val = str(change['old']).replace('_', ' ').title()
            new_val = str(change['new']).replace('_', ' ').title()
            formatted.append(f"- {field_name}: {old_val} -> {new_val}")
    
    return '\n'.join(formatted) if formatted else "Account information updated"


# Event-specific notification functions

def notify_plan_change(tenant, old_plan, new_plan, changed_by):
    """Notify tenant of plan change"""
    changes = {'plan': {'old': old_plan, 'new': new_plan}}
    return send_tenant_notification(tenant, 'plan_change', changes, changed_by)


def notify_trial_expiry(tenant, changed_by=None):
    """Notify tenant of trial expiry"""
    return send_tenant_notification(tenant, 'trial_expiry', None, changed_by)


def notify_status_change(tenant, old_status, new_status, changed_by):
    """Notify tenant of status change"""
    changes = {'status': {'old': old_status, 'new': new_status}}
    return send_tenant_notification(tenant, 'status_change', changes, changed_by)


def notify_email_limit_change(tenant, old_limit, new_limit, changed_by):
    """Notify tenant of email limit change"""
    changes = {'monthly_email_limit': {'old': old_limit, 'new': new_limit}}
    return send_tenant_notification(tenant, 'email_limit_change', changes, changed_by)


def notify_subscription_renewal(tenant, changed_by):
    """Notify tenant of subscription renewal"""
    return send_tenant_notification(tenant, 'subscription_renewal', None, changed_by)


def notify_generic_update(tenant, changes, changed_by):
    """Notify tenant of generic account updates"""
    return send_tenant_notification(tenant, 'generic_update', changes, changed_by)
"""
Enhanced Multi-Tenant Batch Email Tasks
Integrates with the multi-tenant email service for better email handling
"""
import logging
import traceback
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from celery import shared_task
from celery.exceptions import Retry

from .models import Batch, BatchRecipient
from core.models import UserEmailConfiguration
from core.email_service import MultiTenantEmailService
from logs.models import EmailLog

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_batch_emails_multitenant(self, batch_id):
    """Process all emails in a batch with multi-tenant email support"""
    try:
        with transaction.atomic():
            batch = Batch.objects.select_for_update().get(id=batch_id)
            
            if batch.status == 'completed':
                logger.info(f"Batch {batch_id} already completed, skipping processing")
                return
            
            batch.status = 'processing'
            batch.started_at = timezone.now()
            batch.save()
        
        logger.info(f"Starting processing batch {batch_id} with {batch.emails.count()} emails")
        
        # Get tenant's email configuration
        tenant = batch.tenant
        
        try:
            # Find email configuration for users in this tenant
            email_config = UserEmailConfiguration.objects.filter(
                user__tenant=tenant,
                is_active=True
            ).first()
            
            if not email_config:
                # Fallback: try to find default config for any user in tenant
                email_config = UserEmailConfiguration.objects.filter(
                    user__tenant=tenant,
                    is_default=True
                ).first()
            
            if not email_config:
                raise ValueError(f"No active email configuration found for users in tenant {tenant.name}")
            
            # Validate configuration
            is_valid, validation_message = MultiTenantEmailService.validate_configuration(email_config)
            if not is_valid:
                raise ValueError(f"Email configuration invalid: {validation_message}")
            
            logger.info(f"Using email provider: {email_config.provider} for tenant: {tenant.name}")
            
        except Exception as e:
            error_msg = f"Email configuration error for tenant {tenant.name}: {str(e)}"
            logger.error(error_msg)
            
            batch.status = 'failed'
            batch.error_message = error_msg
            batch.completed_at = timezone.now()
            batch.save()
            return
        
        # Process emails
        emails = batch.emails.filter(status='pending')
        total_emails = emails.count()
        processed_count = 0
        failed_count = 0
        
        for email in emails:
            try:
                # Send email using multi-tenant service
                result = send_individual_email_multitenant(
                    email_id=email.id,
                    batch_id=batch_id,
                    email_config_id=email_config.id
                )
                
                if result:
                    processed_count += 1
                    logger.info(f"Successfully sent email {email.id} to {email.recipient_email}")
                else:
                    failed_count += 1
                    logger.error(f"Failed to send email {email.id} to {email.recipient_email}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing email {email.id}: {str(e)}")
                
                # Update email status
                email.status = 'failed'
                email.error_message = str(e)
                email.save()
        
        # Update batch status
        with transaction.atomic():
            batch = Batch.objects.select_for_update().get(id=batch_id)
            batch.emails_sent = processed_count
            batch.emails_failed = failed_count
            batch.completed_at = timezone.now()
            
            if failed_count == 0:
                batch.status = 'completed'
            elif processed_count == 0:
                batch.status = 'failed'
                batch.error_message = f"All {total_emails} emails failed to send"
            else:
                batch.status = 'partial'
                batch.error_message = f"{failed_count} out of {total_emails} emails failed"
            
            batch.save()
        
        logger.info(f"Batch {batch_id} processing completed. Sent: {processed_count}, Failed: {failed_count}")
        
    except Batch.DoesNotExist:
        logger.error(f"Batch {batch_id} not found")
        
    except Exception as e:
        logger.error(f"Critical error processing batch {batch_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        try:
            batch = Batch.objects.get(id=batch_id)
            batch.status = 'failed'
            batch.error_message = f"Critical error: {str(e)}"
            batch.completed_at = timezone.now()
            batch.save()
        except:
            pass
        
        raise self.retry(countdown=60, exc=e)


def send_individual_email_multitenant(email_id, batch_id, email_config_id, retry_count=0):
    """
    Send individual email with retry logic using tenant's email configuration
    """
    max_retries = 3
    
    try:
        # Get email and configuration
        email = BatchEmail.objects.get(id=email_id)
        email_config = UserEmailConfiguration.objects.get(id=email_config_id)
        
        if email.status == 'sent':
            logger.info(f"Email {email_id} already sent, skipping")
            return True
        
        # Update email status
        email.status = 'sending'
        email.attempts += 1
        email.save()
        
        # Development mode handling
        if settings.DEBUG and getattr(settings, 'EMAIL_BACKEND', '') == 'django.core.mail.backends.console.EmailBackend':
            # Simulate sending in development
            logger.info(f"Development mode: Simulating email send for {email.recipient_email}")
            
            # Log to console
            print(f"\n" + "="*80)
            print(f"📧 DEVELOPMENT EMAIL - BATCH {batch_id}")
            print(f"="*80)
            print(f"Provider: {email_config.provider}")
            print(f"From: {email_config.from_email}")
            print(f"To: {email.recipient_email}")
            print(f"Subject: {email.subject}")
            print(f"-"*80)
            print(email.body)
            print(f"="*80)
            
            # Update email status
            email.status = 'sent'
            email.sent_at = timezone.now()
            email.save()
            
            # Create email log
            EmailLog.objects.create(
                batch_email=email,
                tenant=email.batch.tenant,
                recipient_email=email.recipient_email,
                subject=email.subject,
                status='sent',
                provider=email_config.provider,
                sent_at=timezone.now(),
                message="Development mode - simulated send"
            )
            
            return True
        
        # Production mode - actual sending
        try:
            result = MultiTenantEmailService.send_email(
                email_config=email_config,
                subject=email.subject,
                body=email.body,
                to_email=email.recipient_email,
                from_name=email_config.from_name,
                is_html=True
            )
            
            if result:
                # Email sent successfully
                email.status = 'sent'
                email.sent_at = timezone.now()
                email.save()
                
                # Create success log
                EmailLog.objects.create(
                    batch_email=email,
                    tenant=email.batch.tenant,
                    recipient_email=email.recipient_email,
                    subject=email.subject,
                    status='sent',
                    provider=email_config.provider,
                    sent_at=timezone.now(),
                    message="Email sent successfully"
                )
                
                logger.info(f"Email {email_id} sent successfully to {email.recipient_email} via {email_config.provider}")
                return True
            
            else:
                raise Exception("Email sending returned False")
                
        except Exception as send_error:
            logger.error(f"Email sending failed for {email_id}: {str(send_error)}")
            
            # Retry logic
            if retry_count < max_retries:
                logger.info(f"Retrying email {email_id} (attempt {retry_count + 1}/{max_retries})")
                return send_individual_email_multitenant(
                    email_id, batch_id, email_config_id, retry_count + 1
                )
            
            # Max retries reached
            email.status = 'failed'
            email.error_message = str(send_error)
            email.save()
            
            # Create failure log
            EmailLog.objects.create(
                batch_email=email,
                tenant=email.batch.tenant,
                recipient_email=email.recipient_email,
                subject=email.subject,
                status='failed',
                provider=email_config.provider,
                error_message=str(send_error),
                message=f"Failed after {max_retries} retries"
            )
            
            return False
            
    except Exception as e:
        logger.error(f"Critical error in send_individual_email_multitenant: {str(e)}")
        logger.error(traceback.format_exc())
        
        try:
            email = BatchEmail.objects.get(id=email_id)
            email.status = 'failed'
            email.error_message = f"Critical error: {str(e)}"
            email.save()
        except:
            pass
        
        return False


@shared_task
def test_email_configuration(config_id):
    """Test email configuration for a tenant"""
    try:
        email_config = UserEmailConfiguration.objects.get(id=config_id)
        
        # Test configuration
        is_valid, message = MultiTenantEmailService.test_configuration(email_config)
        
        logger.info(f"Email configuration test for {email_config.provider}: {message}")
        return {
            'success': is_valid,
            'message': message,
            'provider': email_config.provider
        }
        
    except Exception as e:
        error_msg = f"Error testing email configuration: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@shared_task
def send_test_email(config_id, test_email):
    """Send a test email using tenant's configuration"""
    try:
        email_config = UserEmailConfiguration.objects.get(id=config_id)
        
        subject = f"Test Email from {email_config.provider}"
        body = f"""
        <h2>Email Configuration Test</h2>
        <p>This is a test email to verify your email configuration.</p>
        <p><strong>Provider:</strong> {email_config.provider}</p>
        <p><strong>From Email:</strong> {email_config.from_email}</p>
        <p><strong>Test Time:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>If you receive this email, your configuration is working correctly!</p>
        """
        
        result = MultiTenantEmailService.send_email(
            email_config=email_config,
            subject=subject,
            body=body,
            to_email=test_email,
            is_html=True
        )
        
        if result:
            logger.info(f"Test email sent successfully to {test_email} via {email_config.provider}")
            return {
                'success': True,
                'message': f'Test email sent successfully to {test_email}',
                'provider': email_config.provider
            }
        else:
            return {
                'success': False,
                'message': 'Test email sending failed',
                'provider': email_config.provider
            }
            
    except Exception as e:
        error_msg = f"Error sending test email: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


@shared_task
def cleanup_old_email_logs():
    """Clean up old email logs"""
    try:
        cutoff_date = timezone.now() - timedelta(days=90)
        old_logs = EmailLog.objects.filter(
            sent_at__lt=cutoff_date
        )
        
        count = old_logs.count()
        old_logs.delete()
        
        logger.info(f"Cleaned up {count} old email logs")
        
    except Exception as e:
        logger.error(f"Error cleaning up old email logs: {str(e)}")


@shared_task
def monitor_email_provider_health():
    """Monitor email provider health and performance"""
    try:
        # Get all active email configurations
        configs = UserEmailConfiguration.objects.filter(is_active=True)
        
        health_report = {}
        
        for config in configs:
            try:
                # Test each configuration
                is_healthy, message = MultiTenantEmailService.test_configuration(config)
                
                health_report[f"{config.tenant.name}_{config.provider}"] = {
                    'healthy': is_healthy,
                    'message': message,
                    'last_checked': timezone.now().isoformat()
                }
                
            except Exception as e:
                health_report[f"{config.tenant.name}_{config.provider}"] = {
                    'healthy': False,
                    'message': str(e),
                    'last_checked': timezone.now().isoformat()
                }
        
        logger.info(f"Email provider health check completed: {len(health_report)} configurations checked")
        return health_report
        
    except Exception as e:
        logger.error(f"Error monitoring email provider health: {str(e)}")
        return {}


# Backward compatibility - keep existing task names
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_batch_emails(self, batch_id):
    """Backward compatibility wrapper for process_batch_emails_multitenant"""
    return process_batch_emails_multitenant(self, batch_id)


def send_individual_email_with_retry_sync(email_id, batch_id, retry_count=0):
    """Backward compatibility wrapper"""
    try:
        # Get the email and find the tenant's config
        email = BatchEmail.objects.get(id=email_id)
        email_config = UserEmailConfiguration.objects.filter(
            tenant=email.batch.tenant,
            is_active=True
        ).first()
        
        if not email_config:
            logger.error(f"No email configuration found for tenant {email.batch.tenant.name}")
            return False
        
        return send_individual_email_multitenant(email_id, batch_id, email_config.id, retry_count)
        
    except Exception as e:
        logger.error(f"Error in backward compatibility wrapper: {str(e)}")
        return False

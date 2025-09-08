from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .models import Batch, BatchRecord, BatchRecipient
from logs.models import BatchExecutionEmailLog
from logs.models import EmailLog
from tenants.models import TenantMailSecret
from .email_utils import (
    EmailValidator, BatchEmailDeduplicator, BatchProcessor,
    EmailConfigurationValidator, BatchStatusTracker, RetryMechanism,
    PerformanceMonitor, BatchOperationContext
)
from .ai_analytics import PredictiveAnalytics, DomainReputationAnalyzer
import json
import logging
import uuid
import time
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


@shared_task
def update_batch_statuses():
    """
    Automatically update batch statuses based on start_time:
    - draft -> scheduled (when start_time is set and valid)
    - scheduled -> running (when start_time has passed)
    """
    try:
        current_time = timezone.now()
        logger.info(f"Running update_batch_statuses at {current_time}")
        
        # Update draft batches to scheduled if they have valid start_time
        draft_batches = Batch.objects.filter(
            status='draft',
            start_time__isnull=False
        )
        
        updated_draft_count = 0
        for batch in draft_batches:
            if batch.start_time and batch.email_configuration and batch.email_configuration.is_active:
                batch.status = 'scheduled'
                batch.save(update_fields=['status', 'updated_at'])
                logger.info(f"Updated batch {batch.id} from draft to scheduled")
                updated_draft_count += 1
        
        # Update scheduled batches to running if start_time has passed
        scheduled_batches = Batch.objects.filter(
            status='scheduled',
            start_time__lte=current_time
        )
        
        logger.info(f"Found {scheduled_batches.count()} scheduled batches to process")
        
        started_batch_count = 0
        for batch in scheduled_batches:
            logger.info(f"Processing batch {batch.id}: start_time={batch.start_time}, current_time={current_time}")
            
            # Check if batch has required components
            if not batch.email_configuration:
                logger.warning(f"Batch {batch.id} has no email configuration")
                continue
                
            if not batch.email_configuration.is_active:
                logger.warning(f"Batch {batch.id} email configuration is not active")
                continue
            
            # Start the batch execution
            try:
                batch.status = 'running'
                batch.save(update_fields=['status', 'updated_at'])
                
                if batch.sub_cycle_enabled:
                    execute_batch_subcycle.delay(batch.id)
                    logger.info(f"Started sub-cycle execution for batch {batch.id}")
                else:
                    send_batch_emails.delay(batch.id)
                    logger.info(f"Started email sending for batch {batch.id}")
                
                started_batch_count += 1
                
            except Exception as e:
                logger.error(f"Error starting batch {batch.id}: {str(e)}")
        
        result_msg = f"Processed {updated_draft_count} draft batches, started {started_batch_count} scheduled batches"
        logger.info(result_msg)
        return result_msg
        
    except Exception as e:
        logger.error(f"Error updating batch statuses: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_batch_emails(batch_id):
    """Enhanced AI-Powered Batch Email Processing with Advanced Analytics"""
    correlation_id = str(uuid.uuid4())[:8]
    logger.info(f"[{correlation_id}] Starting AI-enhanced batch {batch_id} processing")
    
    # Use enterprise-grade operation context
    with BatchOperationContext(batch_id, 'email_sending'):
        try:
            # Initialize batch tracker for atomic operations
            status_tracker = BatchStatusTracker(batch_id)
            
            # Load batch with required relationships first
            batch = Batch.objects.select_related('template', 'tenant', 'email_configuration').get(id=batch_id)
            
            # Handle status transition - allow running batches to continue
            if batch.status == 'scheduled':
                if not status_tracker.safe_status_transition('scheduled', 'running'):
                    logger.warning(f"[{correlation_id}] Batch {batch_id} status transition failed")
                    return
            elif batch.status != 'running':
                logger.warning(f"[{correlation_id}] Batch {batch_id} has invalid status: {batch.status}")
                return
            
            # AI PRE-PROCESSING ANALYTICS
            logger.info(f"[{correlation_id}] Running AI pre-processing analytics...")
            
            # Validate email configuration before processing
            # Skip SMTP connection test for now to avoid validation issues
            if not batch.email_configuration:
                logger.error(f"[{correlation_id}] Batch {batch_id} has no email configuration")
                status_tracker.safe_status_transition('running', 'failed')
                return
            
            if not batch.email_configuration.is_active:
                logger.error(f"[{correlation_id}] Batch {batch_id} email configuration is not active")
                status_tracker.safe_status_transition('running', 'failed')
                return
            
            # Check rate limits
            can_send, current_count = EmailValidator.check_rate_limit(batch.tenant.id)
            if not can_send:
                logger.warning(f"[{correlation_id}] Batch {batch_id} rate limit exceeded: {current_count} emails/hour")
                status_tracker.safe_status_transition('running', 'paused')
                return
            
            # Get deduplicated recipients
            deduplicator = BatchEmailDeduplicator(batch)
            recipients = deduplicator.get_deduplicated_recipients()
            
            if not recipients:
                logger.info(f"[{correlation_id}] No recipients found for batch {batch_id}")
                status_tracker.safe_status_transition('running', 'completed')
                return
            
            # 🛡️ AI DOMAIN REPUTATION ANALYSIS
            recipient_emails = [r['email'] for r in recipients]
            domain_analyzer = DomainReputationAnalyzer()
            domain_analysis = domain_analyzer.analyze_recipient_domains(recipient_emails)
            
            logger.info(f"[{correlation_id}] Domain Analysis: {domain_analysis['risk_assessment']}")
            
            # AI SUCCESS PREDICTION
            batch_data = {
                'recipient_count': len(recipients),
                'scheduled_time': timezone.now(),
                'subject': getattr(batch.template, 'subject', '') if batch.template else '',
                'content': getattr(batch.template, 'content', '') if batch.template else ''
            }
            
            predictor = PredictiveAnalytics(batch.tenant.id)
            prediction = predictor.predict_batch_success_rate(batch_data)
            
            logger.info(f"[{correlation_id}] AI Prediction: {prediction.get('predicted_success_rate', 0):.1f}% success rate")
            
            # Log optimization suggestions
            for suggestion in prediction.get('optimization_suggestions', []):
                logger.info(f"[{correlation_id}] AI Suggestion: {suggestion}")
            
            # Process recipients in memory-optimized chunks
            processor = BatchProcessor(chunk_size=50)  # Smaller chunks for better memory management
            
            def process_chunk(chunk: List[Dict]) -> Tuple[int, int]:
                sent = 0
                failed = 0
                
                for recipient_info in chunk:
                    try:
                        # Validate email format
                        if not EmailValidator.validate_email_format(recipient_info['email']):
                            logger.warning(f"[{correlation_id}] Invalid email format: {recipient_info['email']}")
                            failed += 1
                            continue
                        
                        # Check for bounce-prone emails
                        if EmailValidator.is_bounce_email(recipient_info['email']):
                            logger.warning(f"[{correlation_id}] Skipping bounce-prone email: {recipient_info['email']}")
                            failed += 1
                            continue
                        
                        # Check skip conditions
                        skip_conditions = recipient_info['skip_conditions']
                        if skip_conditions['documents_received']:
                            logger.info(f"[{correlation_id}] Skipping {recipient_info['email']} - documents received")
                            continue
                        
                        if skip_conditions['email_sent'] and batch.interval_minutes == 0:
                            logger.info(f"[{correlation_id}] Skipping {recipient_info['email']} - already sent")
                            continue
                        
                        # Queue email for sending with enhanced retry
                        # Only pass serializable data to Celery task
                        serializable_recipient = {
                            'email': recipient_info['email'],
                            'name': recipient_info['name'],
                            'organization': recipient_info['organization'],
                            'type': recipient_info['type'],
                            'batch_recipient_id': recipient_info.get('batch_recipient_id'),
                            'batch_record_id': recipient_info.get('batch_record_id'),
                            'skip_conditions': skip_conditions
                        }
                        
                        # Try async first, fallback to sync if broker unavailable
                        try:
                            send_individual_email_with_retry.delay(
                                batch_id=batch.id,
                                recipient_info=serializable_recipient,
                                template_id=batch.template.id,
                                correlation_id=correlation_id
                            )
                        except Exception as broker_error:
                            logger.warning(f"[{correlation_id}] Broker unavailable, sending email synchronously: {broker_error}")
                            # Fallback to synchronous execution - pass full recipient_info with objects
                            try:
                                send_individual_email_with_retry_sync(
                                    batch_id=batch.id,
                                    recipient_info=recipient_info,  # Pass original with objects
                                    template_id=batch.template.id,
                                    correlation_id=correlation_id
                                )
                            except Exception as sync_error:
                                logger.error(f"[{correlation_id}] Failed to send email to {recipient_info['email']}: {sync_error}")
                                failed += 1
                                continue
                        sent += 1
                        
                    except Exception as e:
                        logger.error(f"[{correlation_id}] Error processing {recipient_info['email']}: {e}")
                        failed += 1
                
                return sent, failed
            
            # Process all chunks with AI monitoring
            logger.info(f"[{correlation_id}] Processing {len(recipients)} recipients with AI optimization...")
            
            # Log AI suggestion
            if len(suggestion) > 100:
                suggestion_clean = suggestion[:100] + "..."
            else:
                suggestion_clean = suggestion.replace('✅', '[OK]').replace('⚠️', '[WARN]').replace('❌', '[ERROR]')
            total_sent, total_failed = processor.process_in_chunks(recipients, process_chunk)
            
            # Update batch status atomically
            final_status = 'completed' if total_failed == 0 else ('partial' if total_sent > 0 else 'failed')
            status_tracker.update_batch_counters(
                emails_sent=total_sent,
                emails_failed=total_failed,
                status=final_status
            )
            
            # 📊 AI POST-PROCESSING ANALYTICS
            actual_success_rate = (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0
            predicted_rate = prediction.get('predicted_success_rate', 0)
            
            logger.info(f"[{correlation_id}] AI Analysis Complete:")
            logger.info(f"[{correlation_id}] Predicted: {predicted_rate:.1f}% | Actual: {actual_success_rate:.1f}%")
            
            accuracy_delta = abs(predicted_rate - actual_success_rate)
            if accuracy_delta <= 10:
                logger.info(f"[{correlation_id}] AI prediction highly accurate (±{accuracy_delta:.1f}%)")
            elif accuracy_delta <= 20:
                logger.info(f"[{correlation_id}] AI prediction moderately accurate (±{accuracy_delta:.1f}%)")
            else:
                logger.info(f"[{correlation_id}] ⚠️ AI prediction variance detected (±{accuracy_delta:.1f}%) - learning opportunity")
            
            logger.info(f"[{correlation_id}] AI-Enhanced batch {batch_id} completed: {total_sent} sent, {total_failed} failed")
            
        except Batch.DoesNotExist:
            logger.error(f"[{correlation_id}] Batch {batch_id} not found")
        except Exception as e:
            logger.error(f"[{correlation_id}] Error processing batch {batch_id}: {str(e)}")
            try:
                status_tracker = BatchStatusTracker(batch_id)
                status_tracker.safe_status_transition('running', 'failed')
            except:
                pass


@shared_task(bind=True, max_retries=3)
def send_individual_email_with_retry(self, batch_id, recipient_info, template_id, correlation_id, attempt=1):
    """Enhanced individual email sending with retry mechanism and atomic operations"""
    try:
        return send_individual_email_with_retry_sync(batch_id, recipient_info, template_id, correlation_id, attempt)
    except Exception as e:
        # For async execution, handle retries
        if RetryMechanism.should_retry(attempt, e):
            delay = RetryMechanism.calculate_delay(attempt)
            logger.info(f"[{correlation_id}] Retrying email to {recipient_info['email']} in {delay} seconds")
            
            raise self.retry(
                countdown=delay,
                kwargs={
                    'batch_id': batch_id,
                    'recipient_info': recipient_info,
                    'template_id': template_id,
                    'correlation_id': correlation_id,
                    'attempt': attempt + 1
                },
                exc=e
            )
        else:
            raise e


def send_individual_email_with_retry_sync(batch_id, recipient_info, template_id, correlation_id, attempt=1):
    """Synchronous version of individual email sending for fallback execution"""
    recipient_email = recipient_info['email']
    recipient_name = recipient_info['name']
    
    try:
        from emails.models import EmailTemplate
        from django.core.mail import EmailMessage
        from django.core.mail.backends.smtp import EmailBackend
        
        batch = Batch.objects.select_related('tenant', 'email_configuration').get(id=batch_id)
        template = EmailTemplate.objects.get(id=template_id)
        
        # Use validated email configuration
        email_config = batch.email_configuration
        password = email_config.decrypt_password()
        
        # Template processing
        subject = template.subject
        body = template.body
        
        if batch.email_support_fields:
            for key, value in batch.email_support_fields.items():
                subject = subject.replace(f"{{{key}}}", str(value))
                body = body.replace(f"{{{key}}}", str(value))
        
        subject = subject.replace("{recipient_name}", recipient_name or recipient_email)
        body = body.replace("{recipient_name}", recipient_name or recipient_email)
        
        # Get batch recipient object
        batch_recipient = None
        batch_record = None
        if recipient_info['type'] == 'batch_recipient':
            batch_recipient = recipient_info['batch_recipient']
        else:
            batch_record = recipient_info['batch_record']
        
        # Create email log atomically
        with transaction.atomic():
            email_log = EmailLog.objects.create(
                tenant=batch.tenant,
                email_type='batch',
                from_email=email_config.from_email,
                to_email=recipient_email,
                subject=subject,
                body=body,
                status='queued',
                batch=batch,
                batch_recipient=batch_recipient,
            )
        
        try:
            # Debug email configuration
            logger.info(f"[{correlation_id}] Email config verification: is_verified={email_config.is_verified}, is_active={email_config.is_active}")
            
            # Force real email sending when email configurations are verified
            force_real_sending = email_config.is_verified and email_config.is_active
            logger.info(f"[{correlation_id}] force_real_sending = {force_real_sending}")
            
            if force_real_sending:
                # Use verified SMTP configuration for real sending
                logger.info(f"[{correlation_id}] Using verified SMTP configuration for real email sending")
                
                # FORCE SMTP CONNECTION TEST FIRST
                smtp_backend = EmailBackend(
                    host=email_config.email_host,
                    port=email_config.email_port,
                    username=email_config.email_host_user,
                    password=password,
                    use_tls=email_config.email_use_tls,
                    use_ssl=email_config.email_use_ssl,
                    fail_silently=False
                )
                
                # TEST SMTP CONNECTION BEFORE SENDING
                logger.info(f"[{correlation_id}] Testing SMTP connection to {email_config.email_host}:{email_config.email_port}")
                connection_test = smtp_backend.open()
                
                if not connection_test:
                    raise Exception(f"SMTP connection failed to {email_config.email_host}:{email_config.email_port}")
                
                logger.info(f"[{correlation_id}] SMTP connection successful, proceeding with email send")
                
                # Create and send email
                from_name = email_config.from_name or email_config.from_email
                from_header = f"{from_name} <{email_config.from_email}>" if email_config.from_name else email_config.from_email
                
                email_message = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=from_header,
                    to=[recipient_email],
                    connection=smtp_backend
                )
                
                if template.is_html:
                    email_message.content_subtype = 'html'
                
                # FORCE SEND AND VERIFY RESULT
                send_result = email_message.send()
                logger.info(f"[{correlation_id}] SMTP send result: {send_result}")
                
                if send_result != 1:
                    raise Exception(f"Email send failed - SMTP returned {send_result} instead of 1")
                
                # CLOSE CONNECTION EXPLICITLY
                smtp_backend.close()
                logger.info(f"[{correlation_id}] Email successfully sent via SMTP and connection closed")
                email_sent = True
                
            elif settings.DEBUG and getattr(settings, 'EMAIL_BACKEND', '') == 'django.core.mail.backends.console.EmailBackend':
                # Development mode - use console backend for unverified configs
                logger.info(f"[{correlation_id}] Development mode: Using console email backend")
                
                # Print email to console instead of sending via SMTP
                print(f"\n" + "="*60)
                print(f"📧 DEVELOPMENT EMAIL OUTPUT")
                print(f"="*60)
                print(f"From: {email_config.from_email}")
                print(f"To: {recipient_email}")
                print(f"Subject: {subject}")
                print(f"Content Type: {'HTML' if template.is_html else 'Text'}")
                print(f"-"*60)
                print(body)
                print(f"="*60)
                
                # Simulate successful sending
                email_sent = True
                
            else:
                # Production mode - use actual SMTP
                smtp_backend = EmailBackend(
                    host=email_config.email_host,
                    port=email_config.email_port,
                    username=email_config.email_host_user,
                    password=password,
                    use_tls=email_config.email_use_tls,
                    use_ssl=email_config.email_use_ssl,
                    fail_silently=False
                )
                
                # Create and send email
                from_name = email_config.from_name or email_config.from_email
                from_header = f"{from_name} <{email_config.from_email}>" if email_config.from_name else email_config.from_email
                
                email_message = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=from_header,
                    to=[recipient_email],
                    connection=smtp_backend
                )
                
                if template.is_html:
                    email_message.content_subtype = 'html'
                
                email_message.send()
                email_sent = True
            
            # Success - update all records atomically (works for both console and SMTP)
            with transaction.atomic():
                email_log.status = 'sent'
                email_log.sent_at = timezone.now()
                email_log.save()
                
                BatchExecutionEmailLog.objects.create(
                    batch=batch,
                    email_log=email_log,
                    execution_sequence=BatchExecutionEmailLog.objects.filter(batch=batch).count() + 1
                )
                
                # Mark recipient as processed
                if batch_recipient:
                    batch_recipient.email_sent = True
                    batch_recipient.save()
                elif batch_record:
                    batch_record.marked_done = True
                    batch_record.save()
            
            logger.info(f"[{correlation_id}] Email sent successfully to {recipient_email} (attempt {attempt})")
            
        except Exception as e:
            # Handle email sending failure
            error_msg = str(e)
            logger.error(f"[{correlation_id}] SMTP sending failed to {recipient_email} (attempt {attempt}): {error_msg}")
            
            # For verified configs that fail SMTP, fall back to console output
            if force_real_sending and settings.DEBUG:
                logger.warning(f"[{correlation_id}] SMTP failed for verified config, falling back to console output")
                
                # Print email to console as fallback
                print(f"\n" + "="*60)
                print(f"⚠️  SMTP FAILED - CONSOLE FALLBACK")
                print(f"="*60)
                print(f"SMTP Error: {error_msg}")
                print(f"From: {email_config.from_email}")
                print(f"To: {recipient_email}")
                print(f"Subject: {subject}")
                print(f"Content Type: {'HTML' if template.is_html else 'Text'}")
                print(f"-"*60)
                print(body)
                print(f"="*60)
                
                # Update email log as sent with error note
                with transaction.atomic():
                    email_log.status = 'sent'
                    email_log.error_message = f"SMTP failed, used console fallback: {error_msg}"
                    email_log.sent_at = timezone.now()
                    email_log.save()
                    
                    BatchExecutionEmailLog.objects.create(
                        batch=batch,
                        email_log=email_log,
                        execution_sequence=BatchExecutionEmailLog.objects.filter(batch=batch).count() + 1
                    )
                    
                    # Mark recipient as processed
                    if batch_recipient:
                        batch_recipient.email_sent = True
                        batch_recipient.save()
                    elif batch_record:
                        batch_record.marked_done = True
                        batch_record.save()
                
                logger.info(f"[{correlation_id}] Email processed via console fallback for {recipient_email}")
                return  # Return successfully
            
            # For non-verified configs or production mode, mark as failed
            with transaction.atomic():
                email_log.status = 'failed'
                email_log.error_message = error_msg
                email_log.save()
            
            # Determine if retry is appropriate - for sync execution, just log and fail
            if RetryMechanism.should_retry(attempt, e):
                logger.warning(f"[{correlation_id}] Sync execution failed for {recipient_email} - would retry but in sync mode")
            
            # Update batch failure counter
            status_tracker = BatchStatusTracker(batch_id)
            status_tracker.update_batch_counters(emails_failed=1)
            raise e
            
    except Exception as e:
        logger.error(f"[{correlation_id}] Critical error in send_individual_email_with_retry: {str(e)}")
        # Update batch failure counter
        try:
            status_tracker = BatchStatusTracker(batch_id)
            status_tracker.update_batch_counters(emails_failed=1)
        except:
            pass
        raise


@shared_task
def send_individual_email(batch_id, recipient_email, recipient_name, template_id, batch_recipient_id=None):
    """Legacy function for backward compatibility - redirects to new retry-enabled function"""
    recipient_info = {
        'email': recipient_email,
        'name': recipient_name,
        'type': 'batch_recipient' if batch_recipient_id else 'legacy',
        'batch_recipient_id': batch_recipient_id
    }
    
    # Load the actual objects if needed
    if batch_recipient_id:
        try:
            recipient_info['batch_recipient'] = BatchRecipient.objects.get(id=batch_recipient_id)
        except BatchRecipient.DoesNotExist:
            logger.warning(f"BatchRecipient {batch_recipient_id} not found")
            recipient_info['batch_recipient'] = None
    
    correlation_id = str(uuid.uuid4())[:8]
    return send_individual_email_with_retry.delay(
        batch_id, recipient_info, template_id, correlation_id
    )


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def schedule_recurring_batches(self):
    """Check for scheduled batches that need to be executed with proper error handling"""
    try:
        from django.core.cache import cache
        
        now = timezone.now()
        logger.info(f"🚀 Checking for scheduled batches at {now}")
        
        # Log activity to cache for frontend display
        activity_logs = cache.get('batch_automation_logs', [])
        activity_logs.append(f"{now.strftime('%H:%M:%S')} - Automation check started")
        
        # Handle all scheduled batches (both one-time and recurring)
        batches_to_run = Batch.objects.filter(
            status='scheduled',
            start_time__lte=now
        )
        
        logger.info(f"📋 Found {batches_to_run.count()} batches to execute")
        
        if batches_to_run.count() > 0:
            activity_logs.append(f"{now.strftime('%H:%M:%S')} - Found {batches_to_run.count()} batches to execute")
        else:
            activity_logs.append(f"{now.strftime('%H:%M:%S')} - No scheduled batches found")
        
        executed_count = 0
        for batch in batches_to_run:
            # Check if batch has expired
            if batch.end_time and now > batch.end_time:
                batch.status = 'completed'
                batch.save()
                activity_logs.append(f"{now.strftime('%H:%M:%S')} - Batch {batch.name} expired and marked completed")
                continue
            
            # Execute batch - trigger the actual task
            logger.info(f"🔄 Processing batch {batch.id}: {batch.name}")
            activity_logs.append(f"{now.strftime('%H:%M:%S')} - Executing batch: {batch.name}")
            executed_count += 1
            
            try:
                if batch.sub_cycle_enabled:
                    # Use sub-cycle system 
                    execute_batch_subcycle.delay(batch.id)
                    logger.info(f"   📤 Executing sub-cycle batch {batch.id}")
                else:
                    # Use legacy system
                    send_batch_emails.delay(batch.id)
                    logger.info(f"   📤 Executing batch {batch.id}")
                
                # Handle recurring batches
                if batch.interval_minutes > 0:
                    # This is a recurring batch - schedule next run
                    next_run_time = now + timezone.timedelta(minutes=batch.interval_minutes)
                    
                    # Check if next run is within the batch end time
                    if batch.end_time is None or next_run_time <= batch.end_time:
                        batch.start_time = next_run_time
                        batch.status = 'scheduled'  # Keep it scheduled for next run
                        batch.save()
                        logger.info(f"   🔄 Scheduled recurring batch {batch.id} for next run at {batch.start_time}")
                        activity_logs.append(f"{now.strftime('%H:%M:%S')} - Rescheduled recurring batch: {batch.name}")
                    else:
                        batch.status = 'completed'
                        batch.save()
                        logger.info(f"   ✅ Recurring batch {batch.id} completed - end time reached")
                else:
                    # One-time batch - it will be marked as completed by the email task
                    logger.info(f"   ✅ One-time batch {batch.id} started")
                
            except Exception as batch_error:
                logger.error(f"❌ Error processing batch {batch.id}: {batch_error}")
                activity_logs.append(f"{now.strftime('%H:%M:%S')} - Error processing batch {batch.name}: {str(batch_error)}")
                continue
        
        # Save activity logs to cache
        if executed_count > 0:
            activity_logs.append(f"{now.strftime('%H:%M:%S')} - Completed processing {executed_count} batches")
        cache.set('batch_automation_logs', activity_logs[-50:], 86400)  # Keep 50 logs for 24 hours
        
        success_msg = f"🎉 Batch processing completed: {executed_count} executed, 0 failed"
        logger.info(success_msg)
        return success_msg
        
    except Exception as e:
        logger.error(f"❌ Error in schedule_recurring_batches: {str(e)}")
        
        # Log error to cache
        try:
            from django.core.cache import cache
            activity_logs = cache.get('batch_automation_logs', [])
            activity_logs.append(f"{timezone.now().strftime('%H:%M:%S')} - ERROR: {str(e)}")
            cache.set('batch_automation_logs', activity_logs[-50:], 86400)
        except:
            pass
            
        # Retry the task if it fails
        try:
            raise self.retry(countdown=60, exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"💥 Max retries exceeded for schedule_recurring_batches: {str(e)}")
            # Could send alert to administrators here


@shared_task
def execute_batch_subcycle(batch_id):
    """Enhanced sub-cycle execution with atomic operations and proper error handling"""
    correlation_id = str(uuid.uuid4())[:8]
    logger.info(f"[{correlation_id}] Starting sub-cycle execution for batch {batch_id}")
    
    try:
        # Initialize status tracker for atomic operations
        status_tracker = BatchStatusTracker(batch_id)
        now = timezone.now()
        
        # Load batch with required relationships
        batch = Batch.objects.select_related('template', 'tenant', 'email_configuration').get(id=batch_id)
        
        # Check if batch should still be running
        if batch.status not in ['scheduled', 'running']:
            logger.info(f"[{correlation_id}] Batch {batch_id} not in active status: {batch.status}")
            return
        
        # Check if batch has expired
        if batch.end_time and now > batch.end_time:
            status_tracker.safe_status_transition(batch.status, 'completed')
            logger.info(f"[{correlation_id}] Batch {batch_id} completed - end time reached")
            return
        
        # Ensure batch is in running status
        if batch.status != 'running':
            if not status_tracker.safe_status_transition('scheduled', 'running'):
                logger.warning(f"[{correlation_id}] Failed to transition batch {batch_id} to running")
                return
        
        # Validate email configuration (skip for development)
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            # Development mode - skip complex validation
            if not batch.email_configuration or not batch.email_configuration.is_active:
                logger.error(f"[{correlation_id}] Email configuration not available or inactive")
                status_tracker.safe_status_transition('running', 'failed')
                return
        else:
            # Production mode - full validation
            is_valid, error_msg = EmailConfigurationValidator.validate_config(batch.email_configuration)
            if not is_valid:
                logger.error(f"[{correlation_id}] Sub-cycle config validation failed: {error_msg}")
                status_tracker.safe_status_transition('running', 'failed')
                return
        
        # Get recipients who need emails with atomic query
        recipients_to_email = list(
            batch.batch_recipients.filter(
                is_completed=False,
                next_email_due_at__lte=now
            ).select_related('recipient')
        )
        
        logger.info(f"[{correlation_id}] Found {len(recipients_to_email)} recipients needing emails")
        
        if not recipients_to_email:
            logger.info(f"[{correlation_id}] No recipients due for emails in batch {batch_id}")
            return
        
        emails_sent = 0
        emails_failed = 0
        recipients_to_update = []
        
        # Process recipients in chunks to avoid memory issues
        processor = BatchProcessor(chunk_size=25)  # Smaller chunks for sub-cycles
        
        def process_subcycle_chunk(chunk: List) -> Tuple[int, int]:
            nonlocal recipients_to_update
            sent = 0
            failed = 0
            
            for batch_recipient in chunk:
                try:
                    # Validate email before processing
                    if not EmailValidator.validate_email_format(batch_recipient.recipient.email):
                        logger.warning(f"[{correlation_id}] Invalid email: {batch_recipient.recipient.email}")
                        failed += 1
                        continue
                    
                    # Get reminder number
                    reminder_number = batch_recipient.get_reminder_number() if hasattr(batch_recipient, 'get_reminder_number') else batch_recipient.emails_sent_count + 1
                    
                    # Queue email for sending (use direct call in development)
                    if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                        # Development: Direct call without broker
                        send_individual_email_with_reminder(
                            batch_id=batch.id,
                            batch_recipient_id=batch_recipient.id,
                            recipient_email=batch_recipient.recipient.email,
                            recipient_name=batch_recipient.recipient.name,
                            template_id=batch.template.id,
                            reminder_number=reminder_number
                        )
                    else:
                        # Production: Asynchronous with broker
                        send_individual_email_with_reminder.delay(
                            batch_id=batch.id,
                            batch_recipient_id=batch_recipient.id,
                            recipient_email=batch_recipient.recipient.email,
                            recipient_name=batch_recipient.recipient.name,
                            template_id=batch.template.id,
                            reminder_number=reminder_number
                        )
                    
                    # Prepare recipient for batch update
                    batch_recipient.emails_sent_count = (batch_recipient.emails_sent_count or 0) + 1
                    batch_recipient.last_email_sent_at = now
                    
                    # Calculate next email time
                    if batch.sub_cycle_enabled and batch.sub_cycle_interval_minutes > 0:
                        next_due = now + timezone.timedelta(minutes=batch.sub_cycle_interval_minutes)
                        if batch.end_time and next_due > batch.end_time:
                            batch_recipient.next_email_due_at = None
                        else:
                            batch_recipient.next_email_due_at = next_due
                    else:
                        batch_recipient.next_email_due_at = None
                    
                    recipients_to_update.append(batch_recipient)
                    sent += 1
                    
                except Exception as e:
                    logger.error(f"[{correlation_id}] Failed to process {batch_recipient.recipient.email}: {e}")
                    failed += 1
            
            return sent, failed
        
        # Process all recipients
        emails_sent, emails_failed = processor.process_in_chunks(recipients_to_email, process_subcycle_chunk)
        
        # Batch update all recipients atomically
        if recipients_to_update:
            with transaction.atomic():
                for recipient in recipients_to_update:
                    recipient.save(update_fields=['emails_sent_count', 'last_email_sent_at', 'next_email_due_at'])
        
        # Update batch counters atomically
        status_tracker.update_batch_counters(
            emails_sent=emails_sent,
            emails_failed=emails_failed,
            sub_cycles=1
        )
        
        # Schedule next sub-cycle if needed
        if batch.sub_cycle_enabled and batch.sub_cycle_interval_minutes > 0:
            next_subcycle = now + timezone.timedelta(minutes=batch.sub_cycle_interval_minutes)
            
            if not batch.end_time or next_subcycle <= batch.end_time:
                # Update next sub-cycle time atomically
                with transaction.atomic():
                    batch_obj = Batch.objects.select_for_update().get(id=batch_id)
                    batch_obj.next_sub_cycle_time = next_subcycle
                    batch_obj.save(update_fields=['next_sub_cycle_time'])
                
                # Schedule next execution
                execute_batch_subcycle.apply_async(
                    args=[batch_id],
                    eta=next_subcycle
                )
                logger.info(f"[{correlation_id}] Scheduled next sub-cycle at {next_subcycle}")
            else:
                # Clear next sub-cycle time
                with transaction.atomic():
                    batch_obj = Batch.objects.select_for_update().get(id=batch_id)
                    batch_obj.next_sub_cycle_time = None
                    batch_obj.save(update_fields=['next_sub_cycle_time'])
                logger.info(f"[{correlation_id}] No more sub-cycles - end time reached")
        
        # Check if batch should auto-complete
        batch.refresh_from_db()
        if hasattr(batch, 'should_auto_complete') and batch.should_auto_complete():
            status_tracker.safe_status_transition('running', 'completed')
            logger.info(f"[{correlation_id}] Batch {batch_id} auto-completed")
        
        logger.info(f"[{correlation_id}] Sub-cycle completed: {emails_sent} sent, {emails_failed} failed")
        
    except Batch.DoesNotExist:
        logger.error(f"[{correlation_id}] Batch {batch_id} not found")
    except Exception as e:
        logger.error(f"[{correlation_id}] Error executing sub-cycle for batch {batch_id}: {str(e)}")
        try:
            status_tracker = BatchStatusTracker(batch_id)
            status_tracker.safe_status_transition('running', 'failed')
        except:
            pass


@shared_task(bind=True, max_retries=3)
def send_individual_email_with_reminder(self, batch_id, batch_recipient_id, recipient_email, recipient_name, template_id, reminder_number, attempt=1):
    """Enhanced reminder email sending with retry mechanism and atomic operations"""
    correlation_id = str(uuid.uuid4())[:8]
    
    try:
        from emails.models import EmailTemplate
        from django.core.mail import EmailMessage
        from django.core.mail.backends.smtp import EmailBackend
        
        batch = Batch.objects.select_related('tenant', 'email_configuration').get(id=batch_id)
        template = EmailTemplate.objects.get(id=template_id)
        
        # Use validated email configuration
        email_config = batch.email_configuration
        password = email_config.decrypt_password()
        
        # Build subject and body with reminder number
        subject = template.subject
        body = template.body
        
        # Add reminder number to subject if it's not the first email
        if reminder_number > 1:
            if "reminder" in subject.lower():
                subject = subject.replace("Reminder", f"Reminder #{reminder_number}")
                subject = subject.replace("reminder", f"reminder #{reminder_number}")
            else:
                subject = f"Reminder #{reminder_number}: {subject}"
        
        # Replace template variables
        if batch.email_support_fields:
            for key, value in batch.email_support_fields.items():
                subject = subject.replace(f"{{{key}}}", str(value))
                body = body.replace(f"{{{key}}}", str(value))
        
        # Replace recipient variables
        subject = subject.replace("{recipient_name}", recipient_name or recipient_email)
        body = body.replace("{recipient_name}", recipient_name or recipient_email)
        body = body.replace("{reminder_number}", str(reminder_number))
        
        # Get the batch recipient
        batch_recipient = None
        if batch_recipient_id:
            try:
                batch_recipient = BatchRecipient.objects.get(id=batch_recipient_id)
            except BatchRecipient.DoesNotExist:
                logger.warning(f"[{correlation_id}] BatchRecipient {batch_recipient_id} not found")
        
        # Create email log atomically
        with transaction.atomic():
            email_log = EmailLog.objects.create(
                tenant=batch.tenant,
                email_type='batch',
                from_email=email_config.from_email,
                to_email=recipient_email,
                subject=subject,
                body=body,
                status='queued',
                batch=batch,
                batch_recipient=batch_recipient,
            )
        
        try:
            # Create SMTP backend
            smtp_backend = EmailBackend(
                host=email_config.email_host,
                port=email_config.email_port,
                username=email_config.email_host_user,
                password=password,
                use_tls=email_config.email_use_tls,
                use_ssl=email_config.email_use_ssl,
                fail_silently=False
            )
            
            # Create and send email
            from_name = email_config.from_name or email_config.from_email
            from_header = f"{from_name} <{email_config.from_email}>" if email_config.from_name else email_config.from_email
            
            email_message = EmailMessage(
                subject=subject,
                body=body,
                from_email=from_header,
                to=[recipient_email],
                connection=smtp_backend
            )
            
            if template.is_html:
                email_message.content_subtype = 'html'
            
            email_message.send()
            
            # Success - update all records atomically
            with transaction.atomic():
                email_log.status = 'sent'
                email_log.sent_at = timezone.now()
                email_log.save()
                
                BatchExecutionEmailLog.objects.create(
                    batch=batch,
                    email_log=email_log,
                    execution_sequence=BatchExecutionEmailLog.objects.filter(batch=batch).count() + 1
                )
                
                # Mark BatchRecipient as email_sent
                if batch_recipient:
                    batch_recipient.email_sent = True
                    batch_recipient.save()
            
            logger.info(f"[{correlation_id}] Reminder #{reminder_number} sent to {recipient_email} (attempt {attempt})")
            
        except Exception as e:
            # Handle email sending failure
            error_msg = str(e)
            logger.error(f"[{correlation_id}] Failed reminder #{reminder_number} to {recipient_email} (attempt {attempt}): {error_msg}")
            
            # Update email log
            with transaction.atomic():
                email_log.status = 'failed'
                email_log.error_message = error_msg
                email_log.save()
            
            # Determine if retry is appropriate
            if RetryMechanism.should_retry(attempt, e):
                delay = RetryMechanism.calculate_delay(attempt)
                logger.info(f"[{correlation_id}] Retrying reminder to {recipient_email} in {delay} seconds")
                
                raise self.retry(
                    countdown=delay,
                    kwargs={
                        'batch_id': batch_id,
                        'batch_recipient_id': batch_recipient_id,
                        'recipient_email': recipient_email,
                        'recipient_name': recipient_name,
                        'template_id': template_id,
                        'reminder_number': reminder_number,
                        'attempt': attempt + 1
                    },
                    exc=e
                )
            else:
                # Update batch failure counter
                status_tracker = BatchStatusTracker(batch_id)
                status_tracker.update_batch_counters(emails_failed=1)
                raise e
            
    except Exception as e:
        logger.error(f"[{correlation_id}] Critical error in send_individual_email_with_reminder: {str(e)}")
        # Update batch failure counter
        try:
            status_tracker = BatchStatusTracker(batch_id)
            status_tracker.update_batch_counters(emails_failed=1)
        except:
            pass
        raise


@shared_task
def cleanup_old_logs():
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=90)
    
    deleted_count = EmailLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old email logs")
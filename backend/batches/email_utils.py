"""
🚀 RecallIQ Enterprise Email Engine - Production-Ready Utilities
💣 Bomb Application - Email Processing Powerhouse

This module contains enterprise-grade utilities for advanced email processing,
batch management, and reliability features that will dominate the market!
"""

import re
import time
import logging
import smtplib
from typing import List, Dict, Tuple, Optional, Any, Iterator, Set
from datetime import datetime, timedelta
from django.db import transaction, connection
from django.utils import timezone
from django.core.mail.backends.smtp import EmailBackend
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class EmailValidator:
    """🎯 Advanced Email Validation with Industry-Leading Accuracy"""
    
    # Enhanced email regex pattern
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Known problematic domains
    BOUNCE_DOMAINS = {
        'tempmail.org', '10minutemail.com', 'guerrillamail.com',
        'mailinator.com', 'yopmail.com', 'throwaway.email',
        'example.com', 'test.com', 'localhost', '127.0.0.1',
        'invalid', 'fake', 'dummy'
    }
    
    # Enterprise domains (high reputation)
    ENTERPRISE_DOMAINS = {
        'gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com',
        'company.com', 'enterprise.com'
    }
    
    @classmethod
    def validate_email_format(cls, email: str) -> bool:
        """
        🔍 Advanced email format validation
        
        Returns:
            bool: True if email format is valid
        """
        if not email or not isinstance(email, str):
            return False
        
        # Use Django's built-in validator first
        try:
            validate_email(email)
        except ValidationError:
            return False
        
        email = email.strip().lower()
        
        # Additional pattern check
        if not cls.EMAIL_PATTERN.match(email):
            return False
        
        # Additional checks
        if email.count('@') != 1:
            return False
        
        local, domain = email.split('@')
        
        # Local part validation
        if len(local) > 64 or len(domain) > 255:
            return False
        
        # Domain validation
        if domain.startswith('.') or domain.endswith('.'):
            return False
        
        return True
    
    @classmethod
    def is_bounce_email(cls, email: str) -> bool:
        """
        ⚠️ Check if email is from a known bounce-prone domain
        
        Returns:
            bool: True if email is likely to bounce
        """
        if not email:
            return True
        
        domain = email.split('@')[-1].lower()
        return domain in cls.BOUNCE_DOMAINS
    
    @classmethod
    def get_email_reputation(cls, email: str) -> str:
        """
        ⭐ Get email domain reputation score
        
        Returns:
            str: 'high', 'medium', 'low', 'unknown'
        """
        if not cls.validate_email_format(email):
            return 'low'
        
        domain = email.split('@')[-1].lower()
        
        if domain in cls.ENTERPRISE_DOMAINS:
            return 'high'
        elif domain in cls.BOUNCE_DOMAINS:
            return 'low'
        else:
            return 'medium'
    
    @classmethod
    def check_rate_limit(cls, tenant_id: int, limit_per_hour: int = 1000) -> Tuple[bool, int]:
        """
        🚦 Advanced rate limiting with tenant-specific controls
        
        Args:
            tenant_id: Tenant identifier
            limit_per_hour: Max emails per hour
            
        Returns:
            Tuple[bool, int]: (can_send, current_count)
        """
        # Try cache first for performance
        cache_key = f"email_rate_limit:tenant:{tenant_id}:hour"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit_per_hour:
            return False, current_count
        
        # Fallback to database for accuracy
        try:
            from logs.models import EmailLog
            one_hour_ago = timezone.now() - timedelta(hours=1)
            db_count = EmailLog.objects.filter(
                tenant_id=tenant_id,
                created_at__gte=one_hour_ago
            ).count()
            
            # Update cache with accurate count
            cache.set(cache_key, db_count, 3600)
            
            if db_count >= limit_per_hour:
                return False, db_count
            
            return True, db_count
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            # Increment cache counter as fallback
            cache.set(cache_key, current_count + 1, 3600)
            return True, current_count + 1


class BatchEmailDeduplicator:
    """🎯 Advanced Deduplication Across Multiple Systems"""
    
    def __init__(self, batch):
        self.batch = batch
        self.correlation_id = str(uuid.uuid4())[:8]
        self.processed_emails: Set[str] = set()
        self.recipient_data: Dict[str, Dict] = {}
    
    def get_deduplicated_recipients(self) -> List[Dict[str, Any]]:
        """
        🔍 Get deduplicated recipients from all systems
        
        Returns:
            List[Dict]: Deduplicated recipient information
        """
        recipients = {}  # Use dict to automatically deduplicate by email
        
        # Process new system recipients (BatchRecipient)
        self._add_batch_recipients(recipients)
        
        # Process legacy system recipients (Group -> GroupEmail)
        self._add_legacy_recipients(recipients)
        
        # Convert to list and add metadata
        result = list(recipients.values())
        
        logger.info(
            f"[{self.correlation_id}] Deduplicated {len(result)} recipients "
            f"for batch {self.batch.id}"
        )
        
        return result
    
    def _add_batch_recipients(self, recipients: Dict[str, Dict]):
        """Add recipients from new BatchRecipient system"""
        batch_recipients = self.batch.batch_recipients.select_related('recipient').all()
        
        for batch_recipient in batch_recipients:
            email = batch_recipient.recipient.email.lower()
            
            if email not in recipients:
                recipients[email] = {
                    'email': batch_recipient.recipient.email,
                    'name': batch_recipient.recipient.name,
                    'organization': batch_recipient.recipient.organization_name or '',
                    'type': 'batch_recipient',
                    'batch_recipient_id': batch_recipient.id,
                    'batch_recipient': batch_recipient,
                    'batch_record': None,
                    'skip_conditions': {
                        'documents_received': batch_recipient.documents_received,
                        'email_sent': batch_recipient.email_sent,
                        'is_completed': batch_recipient.is_completed
                    }
                }
                self.processed_emails.add(email)
    
    def _add_legacy_recipients(self, recipients: Dict[str, Dict]):
        """Add recipients from legacy Group system"""
        from .models import BatchRecord
        
        for batch_group in self.batch.batch_groups.all():
            group_emails = batch_group.group.group_emails.filter(is_active=True)
            
            for group_email in group_emails:
                email = group_email.email.lower()
                
                if email not in recipients:
                    # Get corresponding batch record
                    try:
                        batch_record = BatchRecord.objects.get(
                            batch=self.batch,
                            recipient_email=group_email.email
                        )
                    except BatchRecord.DoesNotExist:
                        # Create BatchRecord for legacy system compatibility
                        batch_record = BatchRecord.objects.create(
                            batch=self.batch,
                            recipient_email=group_email.email,
                            recipient_name=group_email.name
                        )
                    
                    recipients[email] = {
                        'email': group_email.email,
                        'name': group_email.name,
                        'organization': getattr(group_email, 'organization', ''),
                        'type': 'legacy',
                        'batch_recipient_id': None,
                        'batch_recipient': None,
                        'batch_record': batch_record,
                        'skip_conditions': {
                            'documents_received': batch_record.document_received,
                            'email_sent': batch_record.marked_done,
                            'is_completed': batch_record.document_received
                        }
                    }
                    self.processed_emails.add(email)


class BatchProcessor:
    """⚡ Memory-Efficient Batch Processing with Chunking"""
    
    def __init__(self, chunk_size: int = 50):
        self.chunk_size = chunk_size
        self.correlation_id = str(uuid.uuid4())[:8]
    
    def process_in_chunks(self, items: List[Any], processor_func) -> Tuple[int, int]:
        """
        🔄 Process items in memory-efficient chunks
        
        Args:
            items: List of items to process
            processor_func: Function that processes a chunk and returns (success, failure) counts
            
        Returns:
            Tuple[int, int]: (total_success, total_failure)
        """
        total_success = 0
        total_failure = 0
        total_chunks = (len(items) + self.chunk_size - 1) // self.chunk_size
        
        logger.info(
            f"[{self.correlation_id}] Processing {len(items)} items "
            f"in {total_chunks} chunks of {self.chunk_size}"
        )
        
        for i in range(0, len(items), self.chunk_size):
            chunk = items[i:i + self.chunk_size]
            chunk_num = (i // self.chunk_size) + 1
            
            try:
                success, failure = processor_func(chunk)
                total_success += success
                total_failure += failure
                
                logger.info(
                    f"[{self.correlation_id}] Chunk {chunk_num}/{total_chunks}: "
                    f"{success} success, {failure} failure"
                )
                
                # Memory optimization: small delay between chunks for large batches
                if len(items) > self.chunk_size and chunk_num < total_chunks:
                    time.sleep(0.1)
                
            except Exception as e:
                logger.error(
                    f"[{self.correlation_id}] Chunk {chunk_num} processing error: {str(e)}"
                )
                total_failure += len(chunk)
        
        logger.info(
            f"[{self.correlation_id}] Processing complete: "
            f"{total_success} success, {total_failure} failure"
        )
        
        return total_success, total_failure
    
    def process_iterator(self, items_iterator: Iterator[Any], processor_func) -> Tuple[int, int]:
        """
        🔄 Process items from an iterator (memory-efficient for large datasets)
        
        Returns:
            Tuple[int, int]: (total_success, total_failure)
        """
        total_success = 0
        total_failure = 0
        chunk = []
        chunk_num = 0
        
        for item in items_iterator:
            chunk.append(item)
            
            if len(chunk) >= self.chunk_size:
                chunk_num += 1
                try:
                    success, failure = processor_func(chunk)
                    total_success += success
                    total_failure += failure
                    
                    logger.info(
                        f"[{self.correlation_id}] Chunk {chunk_num}: "
                        f"{success} success, {failure} failure"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"[{self.correlation_id}] Chunk {chunk_num} error: {str(e)}"
                    )
                    total_failure += len(chunk)
                
                chunk = []  # Reset chunk
        
        # Process remaining items
        if chunk:
            chunk_num += 1
            try:
                success, failure = processor_func(chunk)
                total_success += success
                total_failure += failure
            except Exception as e:
                logger.error(f"[{self.correlation_id}] Final chunk error: {str(e)}")
                total_failure += len(chunk)
        
        return total_success, total_failure


class PerformanceMonitor:
    """📊 Performance Monitoring and Metrics Collection"""
    
    @classmethod
    def track_batch_performance(cls, batch_id: int, operation: str, duration: float):
        """
        📈 Track batch operation performance
        
        Args:
            batch_id: Batch identifier
            operation: Operation name (e.g., 'email_sending', 'validation')
            duration: Duration in seconds
        """
        cache_key = f"batch_perf:{batch_id}:{operation}"
        
        # Store performance data
        perf_data = {
            'batch_id': batch_id,
            'operation': operation,
            'duration': duration,
            'timestamp': timezone.now().isoformat()
        }
        
        cache.set(cache_key, perf_data, 3600)  # Store for 1 hour
        
        # Log performance metrics
        logger.info(
            f"Performance: Batch {batch_id} {operation} took {duration:.2f}s"
        )
        
        # Alert on slow operations
        if duration > 30:  # 30 seconds threshold
            logger.warning(
                f"Slow operation detected: Batch {batch_id} {operation} took {duration:.2f}s"
            )
    
    @classmethod
    def get_batch_metrics(cls, batch_id: int) -> Dict[str, Any]:
        """
        📊 Get comprehensive batch metrics
        
        Returns:
            Dict: Performance and status metrics
        """
        from .models import Batch
        
        try:
            batch = Batch.objects.get(id=batch_id)
            
            metrics = {
                'batch_id': batch_id,
                'status': batch.status,
                'total_recipients': batch.total_recipients,
                'emails_sent': batch.emails_sent,
                'emails_failed': batch.emails_failed,
                'success_rate': 0,
                'created_at': batch.created_at.isoformat(),
                'updated_at': batch.updated_at.isoformat()
            }
            
            # Calculate success rate
            total_processed = (batch.emails_sent or 0) + (batch.emails_failed or 0)
            if total_processed > 0:
                metrics['success_rate'] = (batch.emails_sent or 0) / total_processed * 100
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting batch metrics: {str(e)}")
            return {}


# 🚀 Enterprise-Grade Context Manager for Batch Operations
class BatchOperationContext:
    """🎯 Context manager for tracking batch operations with comprehensive logging"""
    
    def __init__(self, batch_id: int, operation: str):
        self.batch_id = batch_id
        self.operation = operation
        self.correlation_id = str(uuid.uuid4())[:8]
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        logger.info(
            f"[{self.correlation_id}] Starting {self.operation} for batch {self.batch_id}"
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.info(
                f"[{self.correlation_id}] Completed {self.operation} "
                f"for batch {self.batch_id} in {duration:.2f}s"
            )
            PerformanceMonitor.track_batch_performance(
                self.batch_id, self.operation, duration
            )
        else:
            logger.error(
                f"[{self.correlation_id}] Failed {self.operation} "
                f"for batch {self.batch_id} after {duration:.2f}s: {exc_val}"
            )
        
        return False  # Don't suppress exceptions


class EmailConfigurationValidator:
    """🔧 Enterprise SMTP Configuration Validation & Testing"""
    
    @classmethod
    def validate_config(cls, email_config) -> Tuple[bool, str]:
        """
        ✅ Comprehensive email configuration validation
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            if not email_config:
                return False, "No email configuration provided"
            
            if not email_config.is_active:
                return False, "Email configuration is not active"
            
            # Check required fields
            required_fields = [
                'email_host', 'email_port', 'email_host_user', 'from_email'
            ]
            
            for field in required_fields:
                if not getattr(email_config, field, None):
                    return False, f"Missing required field: {field}"
            
            # Validate email format
            if not EmailValidator.validate_email_format(email_config.from_email):
                return False, "Invalid from_email format"
            
            # Test password decryption
            try:
                password = email_config.decrypt_password()
                if not password:
                    return False, "Failed to decrypt email password"
            except Exception as e:
                return False, f"Password decryption error: {str(e)}"
            
            # Test SMTP connection (optional, cached)
            connection_test = cls._test_smtp_connection(email_config)
            if not connection_test[0]:
                logger.warning(f"SMTP connection test failed: {connection_test[1]}")
                # Don't fail validation for connection issues (might be temporary)
            
            return True, "Configuration valid"
            
        except Exception as e:
            return False, f"Configuration validation error: {str(e)}"
    
    @classmethod
    def test_connection(cls, email_config) -> Tuple[bool, str]:
        """Test email configuration connection (public interface)"""
        return cls._test_smtp_connection(email_config)
    
    @classmethod
    def _test_smtp_connection(cls, email_config, timeout: int = 10) -> Tuple[bool, str]:
        """
        🌐 Test SMTP connection with caching
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        # Check cache first
        cache_key = f"smtp_test:{email_config.id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            password = email_config.decrypt_password()
            
            # Create test backend
            backend = EmailBackend(
                host=email_config.email_host,
                port=email_config.email_port,
                username=email_config.email_host_user,
                password=password,
                use_tls=email_config.email_use_tls,
                use_ssl=email_config.email_use_ssl,
                timeout=timeout,
                fail_silently=False
            )
            
            # Test connection
            connection = backend.open()
            if connection:
                backend.close()
                result = (True, "SMTP connection successful")
            else:
                result = (False, "Failed to establish SMTP connection")
            
            # Cache result for 5 minutes
            cache.set(cache_key, result, 300)
            return result
            
        except Exception as e:
            result = (False, f"SMTP connection error: {str(e)}")
            cache.set(cache_key, result, 60)  # Cache failures for 1 minute
            return result


class BatchStatusTracker:
    """📊 Atomic Batch Status Management with Race Condition Protection"""
    
    def __init__(self, batch_id: int):
        self.batch_id = batch_id
        self.correlation_id = str(uuid.uuid4())[:8]
    
    def safe_status_transition(self, from_status: str, to_status: str) -> bool:
        """
        🔄 Atomic status transition with proper locking
        
        Returns:
            bool: True if transition was successful
        """
        try:
            with transaction.atomic():
                from .models import Batch
                
                # Use select_for_update to prevent race conditions
                batch = Batch.objects.select_for_update().get(id=self.batch_id)
                
                # Validate transition
                if batch.status != from_status:
                    logger.warning(
                        f"[{self.correlation_id}] Status transition failed: "
                        f"expected {from_status}, got {batch.status}"
                    )
                    return False
                
                # Perform transition
                batch.status = to_status
                batch.updated_at = timezone.now()
                batch.save(update_fields=['status', 'updated_at'])
                
                logger.info(
                    f"[{self.correlation_id}] Status transition: "
                    f"{from_status} -> {to_status} for batch {self.batch_id}"
                )
                return True
                
        except Exception as e:
            logger.error(
                f"[{self.correlation_id}] Status transition error: {str(e)}"
            )
            return False
    
    def update_batch_counters(self, emails_sent: int = 0, emails_failed: int = 0, 
                            sub_cycles: int = 0, status: Optional[str] = None) -> bool:
        """
        📈 Atomic counter updates with proper locking
        
        Returns:
            bool: True if update was successful
        """
        try:
            with transaction.atomic():
                from .models import Batch
                
                batch = Batch.objects.select_for_update().get(id=self.batch_id)
                
                # Update counters
                if emails_sent > 0:
                    batch.emails_sent = (batch.emails_sent or 0) + emails_sent
                
                if emails_failed > 0:
                    batch.emails_failed = (batch.emails_failed or 0) + emails_failed
                
                if sub_cycles > 0:
                    batch.sub_cycles_completed = (batch.sub_cycles_completed or 0) + sub_cycles
                
                if status:
                    batch.status = status
                
                batch.updated_at = timezone.now()
                batch.save()
                
                logger.info(
                    f"[{self.correlation_id}] Updated batch {self.batch_id}: "
                    f"sent+{emails_sent}, failed+{emails_failed}, cycles+{sub_cycles}"
                )
                return True
                
        except Exception as e:
            logger.error(
                f"[{self.correlation_id}] Counter update error: {str(e)}"
            )
            return False


class RetryMechanism:
    """🔄 Intelligent Retry Strategy with Error Classification"""
    
    # Maximum retry attempts
    MAX_RETRIES = 3
    
    # Base delay in seconds
    BASE_DELAY = 30
    
    # Retryable error patterns
    RETRYABLE_ERRORS = {
        'connection': ['Connection refused', 'timeout', 'network'],
        'temporary': ['temporary failure', 'try again', '4'],
        'rate_limit': ['rate limit', 'too many', 'quota']
    }
    
    # Non-retryable error patterns
    PERMANENT_ERRORS = {
        'auth': ['authentication', 'login', 'password'],
        'invalid': ['invalid recipient', 'user unknown', '5'],
        'blocked': ['blocked', 'blacklist', 'spam']
    }
    
    @classmethod
    def should_retry(cls, attempt: int, exception: Exception) -> bool:
        """
        🤔 Intelligent retry decision based on error type
        
        Returns:
            bool: True if retry is recommended
        """
        if attempt >= cls.MAX_RETRIES:
            return False
        
        error_msg = str(exception).lower()
        
        # Check for permanent errors
        for error_type, patterns in cls.PERMANENT_ERRORS.items():
            if any(pattern in error_msg for pattern in patterns):
                logger.info(f"Permanent error detected ({error_type}): {error_msg}")
                return False
        
        # Check for retryable errors
        for error_type, patterns in cls.RETRYABLE_ERRORS.items():
            if any(pattern in error_msg for pattern in patterns):
                logger.info(f"Retryable error detected ({error_type}): {error_msg}")
                return True
        
        # Default: retry for unknown errors (conservative approach)
        return True
    
    @classmethod
    def calculate_delay(cls, attempt: int) -> int:
        """
        ⏰ Exponential backoff with jitter
        
        Returns:
            int: Delay in seconds
        """
        # Exponential backoff: 30s, 60s, 120s
        delay = cls.BASE_DELAY * (2 ** (attempt - 1))
        
        # Add jitter (±25%)
        import random
        jitter = random.uniform(0.75, 1.25)
        
        # Cap at 300 seconds (5 minutes)
        return min(int(delay * jitter), 300)


class EmailConfigurationValidator:
    """🔧 Enterprise SMTP Configuration Validation & Testing"""
    
    @classmethod
    def validate_config(cls, email_config) -> Tuple[bool, str]:
        """
        ✅ Comprehensive email configuration validation
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            if not email_config:
                return False, "No email configuration provided"
            
            if not email_config.is_active:
                return False, "Email configuration is not active"
            
            # Check required fields
            required_fields = [
                'email_host', 'email_port', 'email_host_user', 'from_email'
            ]
            
            for field in required_fields:
                if not getattr(email_config, field, None):
                    return False, f"Missing required field: {field}"
            
            # Validate email format
            if not EmailValidator.validate_email_format(email_config.from_email):
                return False, "Invalid from_email format"
            
            # Test password decryption
            try:
                password = email_config.decrypt_password()
                if not password:
                    return False, "Failed to decrypt email password"
            except Exception as e:
                return False, f"Password decryption error: {str(e)}"
            
            # Test SMTP connection (optional, cached)
            connection_test = cls._test_smtp_connection(email_config)
            if not connection_test[0]:
                logger.warning(f"SMTP connection test failed: {connection_test[1]}")
                # Don't fail validation for connection issues (might be temporary)
            
            return True, "Configuration valid"
            
        except Exception as e:
            return False, f"Configuration validation error: {str(e)}"
    
    @classmethod
    def test_connection(cls, email_config) -> Tuple[bool, str]:
        """Test email configuration connection (public interface)"""
        return cls._test_smtp_connection(email_config)
    
    @classmethod
    def _test_smtp_connection(cls, email_config, timeout: int = 10) -> Tuple[bool, str]:
        """
        🌐 Test SMTP connection with caching
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        # Check cache first
        cache_key = f"smtp_test:{email_config.id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            password = email_config.decrypt_password()
            
            # Create test backend
            from django.core.mail.backends.smtp import EmailBackend
            backend = EmailBackend(
                host=email_config.email_host,
                port=email_config.email_port,
                username=email_config.email_host_user,
                password=password,
                use_tls=email_config.email_use_tls,
                use_ssl=email_config.email_use_ssl,
                timeout=timeout,
                fail_silently=False
            )
            
            # Test connection
            connection = backend.open()
            if connection:
                backend.close()
                result = (True, "SMTP connection successful")
            else:
                result = (False, "Failed to establish SMTP connection")
            
            # Cache result for 5 minutes
            from django.core.cache import cache
            cache.set(cache_key, result, 300)
            return result
            
        except Exception as e:
            result = (False, f"SMTP connection error: {str(e)}")
            from django.core.cache import cache
            cache.set(cache_key, result, 60)  # Cache failures for 1 minute
            return result
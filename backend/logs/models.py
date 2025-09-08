from django.db import models
from django.db.models import F
from tenants.models import Tenant
from batches.models import Batch, BatchRecipient


class EmailLog(models.Model):
    EMAIL_TYPE_CHOICES = [
        ('batch', 'Batch Email'),
        ('test', 'Test Email'),
        ('manual', 'Manual Email'),
        ('welcome', 'Welcome Email'),
        ('notification', 'Admin Notification'),
    ]
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
        ('spam', 'Marked as Spam'),
    ]
    
    DIRECTION_CHOICES = [
        ('outgoing', 'Outgoing (Sent by tenant)'),
        ('incoming', 'Incoming (Received by tenant)'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='email_logs')
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='outgoing', help_text="Whether this email was sent by or received by the tenant")
    from_email = models.EmailField()
    to_email = models.EmailField()
    subject = models.CharField(max_length=500)
    body = models.TextField()
    error_message = models.TextField(blank=True)
    
    # Link to batch and recipient
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    batch_recipient = models.ForeignKey(BatchRecipient, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    
    # Track who sent the email and if it counts against limits
    sent_by_user = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_emails')
    counts_against_limit = models.BooleanField(default=True, help_text="Whether this email counts against tenant's email limit")
    
    # Document status
    documents_received = models.BooleanField(default=False)
    documents_received_at = models.DateTimeField(null=True, blank=True)
    documents_received_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='documents_received')
    
    metadata = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_documents_received(self, user):
        """Mark that documents were received for this email"""
        from django.utils import timezone
        self.documents_received = True
        self.documents_received_at = timezone.now()
        self.documents_received_by = user
        self.save()
        
        # Update the batch recipient status using the proper method
        if self.batch_recipient:
            self.batch_recipient.mark_completed(user)
    
    class Meta:
        db_table = 'email_logs'
        indexes = [
            models.Index(fields=['tenant', 'email_type', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.to_email} - {self.status}"


class BatchExecutionEmailLog(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='execution_logs')
    email_log = models.ForeignKey(EmailLog, on_delete=models.CASCADE, related_name='batch_executions')
    execution_sequence = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'batch_execution_email_logs'
        unique_together = ['batch', 'email_log']
    
    def __str__(self):
        return f"{self.batch.name} - {self.email_log.to_email}"
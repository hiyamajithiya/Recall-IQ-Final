from django.db import models
from tenants.models import Tenant, Group
from emails.models import EmailTemplate
from core.models import UserEmailConfiguration
from core.models_recipients import Recipient, ContactGroup
import json


class Batch(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    INTERVAL_CHOICES = [
        ('none', 'No Repeat'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    SUB_CYCLE_INTERVAL_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='batches')
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='batches')
    email_configuration = models.ForeignKey(UserEmailConfiguration, on_delete=models.CASCADE, related_name='batches', null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    interval_minutes = models.PositiveIntegerField(default=0)
    email_support_fields = models.JSONField(default=dict, blank=True)
    total_recipients = models.PositiveIntegerField(default=0)
    emails_sent = models.PositiveIntegerField(default=0)
    emails_failed = models.PositiveIntegerField(default=0)
    
    # Sub-cycle email sending fields
    sub_cycle_enabled = models.BooleanField(
        default=False,
        help_text="Enable repeated emails until documents received"
    )
    sub_cycle_interval_type = models.CharField(
        max_length=20, 
        choices=SUB_CYCLE_INTERVAL_CHOICES, 
        default='daily',
        help_text="Type of sub-cycle interval"
    )
    sub_cycle_interval_minutes = models.PositiveIntegerField(
        default=1440,  # Daily by default
        help_text="Custom interval in minutes for sub-cycle"
    )
    sub_cycle_interval_days = models.PositiveIntegerField(
        default=1,  # 1 day by default for custom
        null=True, blank=True,
        help_text="Custom interval in days for sub-cycle (only used when interval_type is 'custom')"
    )
    auto_complete_on_all_received = models.BooleanField(
        default=True,
        help_text="Auto-complete batch when all recipients submit documents"
    )
    
    # Sub-cycle tracking fields
    next_sub_cycle_time = models.DateTimeField(
        null=True, blank=True,
        help_text="When next sub-cycle should run"
    )
    sub_cycles_completed = models.PositiveIntegerField(
        default=0,
        help_text="Number of sub-cycles executed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'batches'
    
    def __str__(self):
        return f"{self.tenant.name} - {self.name}"


class BatchRecipient(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='batch_recipients')
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, related_name='batch_recipients')
    documents_received = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    
    # Sub-cycle tracking fields
    emails_sent_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of emails sent to this recipient"
    )
    last_email_sent_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When last email was sent to this recipient"
    )
    next_email_due_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When next email should be sent to this recipient"
    )
    is_completed = models.BooleanField(
        default=False,
        help_text="Whether this recipient has completed (documents received)"
    )
    completed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When documents were received from this recipient"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'batch_recipients'
        unique_together = ('batch', 'recipient')

    def __str__(self):
        return f"{self.batch.name} - {self.recipient.email}"
    
    def mark_completed(self, user=None):
        """Mark this recipient as completed (documents received)"""
        from django.utils import timezone
        self.is_completed = True
        self.documents_received = True
        self.completed_at = timezone.now()
        self.next_email_due_at = None  # Stop future emails
        self.save()
    
    def get_reminder_number(self):
        """Get the current reminder number for this recipient"""
        return self.emails_sent_count + 1


# Move Batch methods back to the Batch class
def batch_interval_type(self):
    """Convert interval_minutes to user-friendly interval type"""
    if self.interval_minutes == 0:
        return 'none'
    elif self.interval_minutes == 24 * 60:  # 1440 minutes = 1 day
        return 'daily'
    elif self.interval_minutes == 7 * 24 * 60:  # 10080 minutes = 1 week
        return 'weekly'
    elif self.interval_minutes == 30 * 24 * 60:  # 43200 minutes = 30 days (approximately 1 month)
        return 'monthly'
    elif self.interval_minutes == 365 * 24 * 60:  # 525600 minutes = 365 days (1 year)
        return 'yearly'
    else:
        return 'custom'

# Add these methods to Batch class
Batch.interval_type = property(batch_interval_type)

def batch_set_interval_type(self, interval_type):
    """Set interval_minutes based on interval type"""
    interval_mapping = {
        'none': 0,
        'daily': 24 * 60,  # 1440 minutes
        'weekly': 7 * 24 * 60,  # 10080 minutes
        'monthly': 30 * 24 * 60,  # 43200 minutes
        'yearly': 365 * 24 * 60,  # 525600 minutes
    }
    self.interval_minutes = interval_mapping.get(interval_type, 0)

Batch.set_interval_type = batch_set_interval_type

def batch_set_sub_cycle_interval_minutes(self, interval_type, custom_minutes=None):
    """Set sub_cycle_interval_minutes based on interval type"""
    if interval_type == 'custom' and custom_minutes:
        self.sub_cycle_interval_minutes = custom_minutes
    else:
        interval_mapping = {
            'daily': 24 * 60,  # 1440 minutes
            'weekly': 7 * 24 * 60,  # 10080 minutes  
            'monthly': 30 * 24 * 60,  # 43200 minutes
        }
        self.sub_cycle_interval_minutes = interval_mapping.get(interval_type, 1440)

Batch.set_sub_cycle_interval_minutes = batch_set_sub_cycle_interval_minutes

def batch_get_sub_cycle_interval_display(self):
    """Get human-readable sub-cycle interval"""
    if self.sub_cycle_interval_type == 'custom':
        hours = self.sub_cycle_interval_minutes // 60
        if hours >= 24:
            days = hours // 24
            return f"Every {days} day{'s' if days != 1 else ''}"
        else:
            return f"Every {hours} hour{'s' if hours != 1 else ''}"
    return dict(self.SUB_CYCLE_INTERVAL_CHOICES).get(self.sub_cycle_interval_type, 'Daily')

Batch.get_sub_cycle_interval_display = batch_get_sub_cycle_interval_display

def batch_should_auto_complete(self):
    """Check if batch should auto-complete based on recipient completion"""
    if not self.auto_complete_on_all_received:
        return False
    
    incomplete_count = self.batch_recipients.filter(is_completed=False).count()
    return incomplete_count == 0

Batch.should_auto_complete = batch_should_auto_complete

def batch_add_recipients(self, recipients=None, contact_groups=None):
    """
    Add recipients to the batch, either directly or from contact groups
    """
    from django.utils import timezone
    
    if recipients:
        batch_recipients = []
        for recipient in recipients:
            if not self.batch_recipients.filter(recipient=recipient).exists():
                batch_recipients.append(
                    BatchRecipient(
                        batch=self, 
                        recipient=recipient,
                        next_email_due_at=self.start_time  # First email at batch start
                    )
                )
        if batch_recipients:
            BatchRecipient.objects.bulk_create(batch_recipients)
    
    if contact_groups:
        recipients_from_groups = Recipient.objects.filter(
            groups__in=contact_groups,
            tenant=self.tenant
        ).distinct()
        
        batch_recipients = []
        for recipient in recipients_from_groups:
            if not self.batch_recipients.filter(recipient=recipient).exists():
                batch_recipients.append(
                    BatchRecipient(
                        batch=self, 
                        recipient=recipient,
                        next_email_due_at=self.start_time  # First email at batch start
                    )
                )
        if batch_recipients:
            BatchRecipient.objects.bulk_create(batch_recipients)
    
    # Update total recipients count
    self.total_recipients = self.batch_recipients.count()
    self.save(update_fields=['total_recipients'])

Batch.add_recipients = batch_add_recipients


# Remove the misplaced methods section
class BatchGroup(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='batch_groups')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='batch_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'batch_groups'
        unique_together = ['batch', 'group']
    
    def __str__(self):
        return f"{self.batch.name} - {self.group.name}"


class BatchRecord(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='batch_records')
    recipient_email = models.EmailField()
    recipient_name = models.CharField(max_length=255, blank=True)
    document_received = models.BooleanField(default=False)
    marked_done = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'batch_records'
        unique_together = ['batch', 'recipient_email']
    
    def __str__(self):
        return f"{self.batch.name} - {self.recipient_email}"
from django.db import models
from cryptography.fernet import Fernet
from django.conf import settings
import json


class Tenant(models.Model):
    PLAN_CHOICES = [
        ('starter', 'Starter Plan'),
        ('professional', 'Professional Plan'),
        ('enterprise', 'Enterprise Plan'),
        ('custom', 'Custom Plan'),
    ]
    
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)
    
    # SaaS Subscription Fields
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='starter')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    monthly_email_limit = models.IntegerField(default=1000)
    emails_sent_this_month = models.IntegerField(default=0)
    
    # Company Details - Now mandatory
    company_address = models.TextField(help_text="Company address is required")
    contact_person = models.CharField(max_length=255, help_text="Contact person name is required")
    contact_email = models.EmailField(help_text="Contact email is required")
    contact_phone = models.CharField(max_length=20, help_text="Contact phone is required")
    
    # Billing
    billing_email = models.EmailField(blank=True, help_text="Will auto-fill with contact email if not provided")
    payment_method = models.CharField(max_length=50, blank=True)
    
    # User Limits - Manually configured by Super Admin/Sales Team
    max_tenant_admins = models.IntegerField(default=1, help_text="Maximum tenant admin users allowed")
    max_staff_admins = models.IntegerField(default=1, help_text="Maximum staff admin users allowed")
    max_staff_users = models.IntegerField(default=3, help_text="Maximum staff users allowed")
    max_total_users = models.IntegerField(default=5, help_text="Maximum total users allowed for this tenant")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'tenants'
        db_table = 'tenants'
    
    def save(self, *args, **kwargs):
        """Override save to handle auto-fill billing email and auto-expire status"""
        from django.utils import timezone
        
        # Auto-fill billing email with contact email if not provided
        if not self.billing_email and self.contact_email:
            self.billing_email = self.contact_email
        
        # Auto-update status to expired if subscription has ended
        now = timezone.now()
        if self.status == 'active' and self.subscription_end_date and self.subscription_end_date < now:
            self.status = 'expired'
        elif self.status == 'trial' and self.trial_end_date and self.trial_end_date < now:
            self.status = 'expired'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.plan.title()})"
    
    @property
    def is_subscription_active(self):
        from django.utils import timezone
        if self.status == 'active':
            return self.subscription_end_date > timezone.now() if self.subscription_end_date else True
        return False
    
    @property
    def is_trial_active(self):
        from django.utils import timezone
        if self.status == 'trial':
            return self.trial_end_date > timezone.now() if self.trial_end_date else True
        return False
    
    @property
    def days_until_expiry(self):
        from django.utils import timezone
        if self.status == 'trial' and self.trial_end_date:
            delta = self.trial_end_date - timezone.now()
            return max(0, delta.days)
        elif self.status == 'active' and self.subscription_end_date:
            delta = self.subscription_end_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    @property 
    def emails_sent_this_month_countable(self):
        """Count only emails that count against the tenant's limit (excluding admin notifications)"""
        from django.utils import timezone
        from logs.models import EmailLog
        
        # Get first day of current month
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Count emails sent this month that count against limit
        return EmailLog.objects.filter(
            tenant=self,
            created_at__gte=month_start,
            status__in=['sent', 'delivered', 'opened'],
            counts_against_limit=True
        ).count()
    
    @property
    def email_usage_percentage(self):
        if self.monthly_email_limit > 0:
            # Use the new countable method instead of the old field
            emails_sent = self.emails_sent_this_month_countable
            return min(100, (emails_sent / self.monthly_email_limit) * 100)
        return 0
    
    @property
    def is_expired(self):
        """Check if tenant is expired or should be highlighted"""
        from django.utils import timezone
        now = timezone.now()
        
        # Already expired status
        if self.status == 'expired':
            return True
        
        # Active subscription that has ended
        if self.status == 'active' and self.subscription_end_date and self.subscription_end_date < now:
            return True
        
        # Trial that has ended
        if self.status == 'trial' and self.trial_end_date and self.trial_end_date < now:
            return True
        
        return False
    
    @property
    def expires_soon(self):
        """Check if tenant expires within 7 days"""
        return self.days_until_expiry <= 7 and self.days_until_expiry > 0
    
    @property
    def current_user_counts(self):
        """Returns current count of users by role for this tenant"""
        from core.models import User
        
        if not self.pk:  # New tenant not saved yet
            return {
                'tenant_admin': 0,
                'staff_admin': 0, 
                'staff': 0,
                'sales_team': 0,
                'total': 0
            }
        
        users = User.objects.filter(tenant=self)
        counts = {
            'tenant_admin': users.filter(role='tenant_admin').count(),
            'staff_admin': users.filter(role='staff_admin').count(),
            'staff': users.filter(role='staff').count(),
            'sales_team': users.filter(role='sales_team').count(),
        }
        counts['total'] = sum(counts.values())
        return counts
    
    def can_add_user(self, role):
        """Check if tenant can add more users of specific role"""
        current_counts = self.current_user_counts
        
        # Check total user limit first
        if current_counts['total'] >= self.max_total_users:
            return False, f"Cannot exceed maximum total users ({self.max_total_users})"
        
        # Check role-specific limits
        if role == 'tenant_admin':
            if current_counts['tenant_admin'] >= self.max_tenant_admins:
                return False, f"Cannot exceed maximum tenant admins ({self.max_tenant_admins})"
        elif role == 'staff_admin':
            if current_counts['staff_admin'] >= self.max_staff_admins:
                return False, f"Cannot exceed maximum staff admins ({self.max_staff_admins})"
        elif role in ['staff', 'sales_team']:
            if current_counts['staff'] + current_counts['sales_team'] >= self.max_staff_users:
                return False, f"Cannot exceed maximum staff users ({self.max_staff_users})"
        
        return True, "User can be added"
    
    @property
    def users_remaining(self):
        """Returns remaining user slots by role"""
        current_counts = self.current_user_counts
        
        return {
            'tenant_admin': max(0, self.max_tenant_admins - current_counts['tenant_admin']),
            'staff_admin': max(0, self.max_staff_admins - current_counts['staff_admin']),
            'staff': max(0, self.max_staff_users - (current_counts['staff'] + current_counts['sales_team'])),
            'total': max(0, self.max_total_users - current_counts['total'])
        }
    
    @property
    def user_usage_percentage(self):
        """Returns percentage of total users used"""
        if self.max_total_users > 0:
            current_total = self.current_user_counts['total']
            return min(100, (current_total / self.max_total_users) * 100)
        return 0


class TenantEmail(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='emails')
    email = models.EmailField()
    display_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'tenants'
        db_table = 'tenant_emails'
        unique_together = ['tenant', 'email']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.email}"


class TenantMailSecret(models.Model):
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail API'),
        ('gmail_smtp', 'Gmail SMTP'),
        ('outlook', 'Microsoft Graph API'),
        ('outlook_smtp', 'Outlook SMTP'),
        ('yahoo', 'Yahoo Mail'),
        ('rediffmail', 'RediffMail'),
        ('hotmail', 'Hotmail'),
        ('aol', 'AOL Mail'),
        ('zoho', 'Zoho Mail'),
        ('icloud', 'iCloud Mail'),
        ('protonmail', 'ProtonMail'),
        ('smtp', 'Generic SMTP'),
    ]
    
    tenant_email = models.OneToOneField(TenantEmail, on_delete=models.CASCADE, related_name='mail_secret')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    encrypted_credentials = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'tenants'
        db_table = 'tenant_mail_secrets'
    
    def encrypt_credentials(self, credentials_dict):
        f = Fernet(settings.ENCRYPTION_KEY.encode())
        credentials_json = json.dumps(credentials_dict)
        self.encrypted_credentials = f.encrypt(credentials_json.encode()).decode()
    
    def decrypt_credentials(self):
        f = Fernet(settings.ENCRYPTION_KEY.encode())
        decrypted_json = f.decrypt(self.encrypted_credentials.encode()).decode()
        return json.loads(decrypted_json)
    
    def __str__(self):
        return f"{self.tenant_email.email} - {self.provider}"


class Group(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'tenants'
        db_table = 'groups'
        unique_together = ['tenant', 'name']
    
    @property
    def email_count(self):
        return self.group_emails.count()
    
    def __str__(self):
        return f"{self.tenant.name} - {self.name}"


class GroupEmail(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_emails')
    email = models.EmailField()
    name = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'tenants'
        db_table = 'group_emails'
        unique_together = ['group', 'email']
    
    def __str__(self):
        return f"{self.group.name} - {self.email}"
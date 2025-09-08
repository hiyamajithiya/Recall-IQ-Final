from django.contrib.auth.models import AbstractUser
from django.db import models
from cryptography.fernet import Fernet
from django.conf import settings
import json

# Import recipient models
from .models_recipients import ContactGroup, Recipient


class User(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('sales_team', 'Sales Team'),
        ('support_team', 'Support Team'),
        ('tenant_admin', 'Tenant Admin'),
        ('staff_admin', 'Staff Admin'),
        ('staff', 'Staff'),
        ('user', 'User'),
    ]

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)

    # Allow login with either username or email
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def save(self, *args, **kwargs):
        # Ensure username is set before saving
        if not self.username and self.email:
            from django.utils.text import slugify
            base_username = self.email.split('@')[0]
            username = slugify(base_username)
            counter = 1
            temp_username = username
            while User.objects.filter(username=temp_username).exists():
                temp_username = f"{username}{counter}"
                counter += 1
            self.username = temp_username
        super().save(*args, **kwargs)

    @classmethod
    def get_by_login(cls, login):
        """Get user by either username or email"""
        if '@' in login:
            return cls.objects.filter(email=login).first()
        return cls.objects.filter(username=login).first()
        
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"


class UserEmailConfiguration(models.Model):
    PROVIDER_CHOICES = [
        ('gmail', 'Gmail API (OAuth 2.0)'),
        ('gmail_smtp', 'Gmail SMTP'),
        ('outlook', 'Microsoft Graph API (OAuth 2.0)'),
        ('outlook_smtp', 'Outlook SMTP'),
        ('yahoo', 'Yahoo Mail SMTP'),
        ('icloud', 'iCloud Mail SMTP'),
        ('zoho', 'Zoho Mail SMTP'),
        ('aol', 'AOL Mail SMTP'),
        ('protonmail', 'ProtonMail Bridge'),
        ('smtp', 'Custom SMTP Server'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_configurations')
    name = models.CharField(max_length=255, help_text="Display name for this email config")
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default='gmail')
    
    # SMTP Settings
    email_host = models.CharField(max_length=255, blank=True)
    email_port = models.IntegerField(default=587)
    email_use_tls = models.BooleanField(default=True)
    email_use_ssl = models.BooleanField(default=False)
    
    # Email Details
    email_host_user = models.EmailField(blank=True)
    encrypted_email_host_password = models.TextField(blank=True)
    from_email = models.EmailField()
    from_name = models.CharField(max_length=255, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_email_configurations'
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.from_email})"
    
    def encrypt_password(self, password):
        """Encrypt email password using Fernet encryption with proper error handling"""
        if not password:
            self.encrypted_email_host_password = ""
            return
            
        try:
            if hasattr(settings, 'ENCRYPTION_KEY') and settings.ENCRYPTION_KEY:
                # Use Fernet encryption with the configured key
                f = Fernet(settings.ENCRYPTION_KEY.encode())
                encrypted = f.encrypt(password.encode()).decode()
                self.encrypted_email_host_password = encrypted
            else:
                # Fallback to base64 encoding (not secure but better than plain text)
                import base64
                self.encrypted_email_host_password = base64.b64encode(password.encode()).decode()
                print("WARNING: Using base64 encoding - ENCRYPTION_KEY not configured")
                
        except Exception as e:
            print(f"Encryption error: {e}")
            # Emergency fallback to prevent data loss
            import base64
            self.encrypted_email_host_password = base64.b64encode(password.encode()).decode()
    
    def decrypt_password(self):
        """Decrypt email password with consistent error handling"""
        if not self.encrypted_email_host_password:
            return ""
            
        try:
            if hasattr(settings, 'ENCRYPTION_KEY') and settings.ENCRYPTION_KEY:
                # Try Fernet decryption first
                try:
                    f = Fernet(settings.ENCRYPTION_KEY.encode())
                    decrypted = f.decrypt(self.encrypted_email_host_password.encode()).decode()
                    return decrypted
                except Exception:
                    # If Fernet fails, try base64 fallback
                    pass
            
            # Try base64 decryption as fallback
            try:
                import base64
                decrypted = base64.b64decode(self.encrypted_email_host_password.encode()).decode()
                return decrypted
            except Exception:
                pass
                
            # If all methods fail, return empty string
            print(f"Failed to decrypt password for config: {self.name}")
            return ""
                    
        except Exception as e:
            print(f"Unexpected decryption error: {e}")
            return ""
    
    def save(self, *args, **kwargs):
        # If this is set as default, make all other configs for this user non-default
        if self.is_default:
            UserEmailConfiguration.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
    
    def __str__(self):
        return f"Reset token for {self.user.username}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()


class EmailOTPVerification(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    # Store signup data temporarily
    signup_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'email_otp_verifications'
    
    def __str__(self):
        return f"OTP for {self.email}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired() and self.attempts < 3
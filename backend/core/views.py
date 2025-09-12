from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
import pytz
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from .serializers import (
    CustomTokenObtainPairSerializer, UserRegistrationSerializer, TenantAdminRegistrationSerializer, 
    UserSerializer, UserProfileUpdateSerializer, UserEmailConfigurationSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer, 
    EmailOTPRequestSerializer, EmailOTPVerifySerializer
)
from .permissions import IsSuperAdmin, IsSuperAdminOrSupportTeam, IsSuperAdminOrSupportTeamNonDestructive, IsTenantAdmin
from .models import UserEmailConfiguration

User = get_user_model()


def get_ist_time(dt=None):
    """
    Convert datetime to IST (Indian Standard Time)
    If no datetime provided, uses current time
    """
    if dt is None:
        dt = timezone.now()
    
    ist_timezone = pytz.timezone('Asia/Kolkata')
    return dt.astimezone(ist_timezone)


def format_ist_time(dt=None, format_string='%B %d, %Y at %I:%M %p IST'):
    """
    Format datetime in IST with given format string
    """
    ist_time = get_ist_time(dt)
    return ist_time.strftime(format_string)


def send_welcome_email(user, password=None, created_by=None):
    """Send welcome email to newly created user with comprehensive credentials and logging"""
    from django.core.mail import EmailMessage
    from django.core.mail.backends.smtp import EmailBackend
    from django.utils import timezone
    from logs.models import EmailLog
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Initialize email log entry
    email_log = None
    
    try:
        print(f"Attempting to send welcome email to: {user.email}")
        logger.info(f"Sending welcome email to {user.email}")
        
        # Validate user email
        if not user.email:
            print(f"User {user.username} does not have an email address")
            return False
        
        # Get tenant for logging (use user's tenant or create a default entry)
        tenant = user.tenant
        if not tenant and user.role != 'super_admin':
            print(f"Warning: User {user.username} has no tenant assigned")
        
        # Get email configuration and backend
        backend = None
        from_email = settings.DEFAULT_FROM_EMAIL
        email_config = None
        email_config_source = "Django Settings"
        
        # Check if Django email settings are properly configured
        django_email_configured = bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)
        print(f"Django email settings configured: {django_email_configured}")
        if not django_email_configured:
            print("Warning: Django EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not set")
        
        try:
            super_admin = User.objects.filter(role='super_admin').first()
            if super_admin:
                email_config = UserEmailConfiguration.objects.filter(
                    user=super_admin, 
                    is_default=True, 
                    is_active=True
                ).first()
                
                if email_config:
                    print(f"Found super admin email config: {email_config.name}")
                    email_config_source = f"Super Admin Config: {email_config.name}"
                    # Use super admin's email configuration
                    try:
                        print(f"Attempting to decrypt password for config: {email_config.name}")
                        print(f"Encrypted password field exists: {bool(email_config.encrypted_email_host_password)}")
                        print(f"Encrypted password field length: {len(email_config.encrypted_email_host_password) if email_config.encrypted_email_host_password else 0}")
                        
                        password_decrypt = email_config.decrypt_password()
                        print(f"Password decrypt result: {'Success' if password_decrypt else 'Failed/Empty'}")
                        print(f"Decrypted password length: {len(password_decrypt) if password_decrypt else 0}")
                        
                        if password_decrypt and password_decrypt.strip():
                            print(f"Setting up custom email backend with decrypted password")
                            backend = EmailBackend(
                                host=email_config.email_host,
                                port=int(email_config.email_port),
                                username=email_config.email_host_user,
                                password=password_decrypt,
                                use_tls=email_config.email_use_tls,
                                use_ssl=email_config.email_use_ssl,
                                fail_silently=False
                            )
                            from_email = email_config.from_email
                            print(f"Email backend configured with host: {email_config.email_host}:{email_config.email_port}")
                            print(f"Using from_email: {from_email}")
                            print(f"Email username: {email_config.email_host_user}")
                        else:
                            print("Failed to decrypt super admin email password or password is empty")
                            print("This indicates the password was not properly encrypted when saved")
                            print("Falling back to Django settings, but will use console backend if Django settings are incomplete")
                            email_config_source = "Django Settings (decrypt failed - password not properly saved)"
                    except Exception as e:
                        print(f"Error setting up super admin email backend: {e}")
                        print(f"Full error details: {repr(e)}")
                        email_config_source = f"Django Settings (config error: {str(e)})"
                else:
                    print("No default email config found for super admin, using Django settings")
                    email_config_source = "Django Settings (no super admin config)"
            else:
                print("No super admin found, using Django settings")
                email_config_source = "Django Settings (no super admin)"
        except Exception as e:
            print(f"Error getting super admin email config: {e}")
            email_config_source = f"Django Settings (error: {str(e)})"
        
        print(f"Email configuration source: {email_config_source}")
        
        # Final check for email configuration validity and fallback to console backend
        if not backend and not django_email_configured:
            print("WARNING: No valid email configuration found - neither super admin config nor Django settings are properly configured!")
            print("Using console email backend for development - emails will be printed to console")
            from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
            backend = ConsoleEmailBackend()
            email_config_source += " - USING CONSOLE BACKEND"
        
        # Prepare comprehensive credential information
        user_full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        company_name = tenant.name if tenant else "RecallIQ Platform"
        
        # Determine login credentials text with all details
        credentials_section = f"""
═══════════════════════════════════════════════════════════════
                            ACCOUNT CREDENTIALS
═══════════════════════════════════════════════════════════════

👤 Personal Information:
   • Full Name: {user_full_name}
   • Email Address: {user.email}
   • Username: {user.username}
   • Role: {user.get_role_display()}

🏢 Company Information:
   • Company Name: {company_name}
   • Tenant ID: {tenant.id if tenant else 'N/A'}
   • Plan: {tenant.get_plan_display() if tenant else 'Platform Access'}
   • Status: {tenant.get_status_display() if tenant else 'Active'}

🔐 Login Credentials:
   • Login URL: {settings.FRONTEND_URL or 'http://localhost:3000'}
   • Email: {user.email}
   • Username: {user.username}"""

        if password:
            # Check if this is a Google OAuth user by seeing if they have no password history
            is_google_oauth = not hasattr(user, 'date_joined') or user.date_joined == user.last_login
            if created_by is None and user.role == 'tenant_admin':
                # This might be a Google OAuth signup
                credentials_section += f"""
   • Password: {password}
   
⚠️  SECURITY NOTICE FOR GOOGLE OAUTH USERS:
   Since you signed up with Google OAuth, we've generated a secure password for your account.
   You can continue using Google Sign-In OR use this password for regular login.
   For enhanced security, please change this password after your first login."""
            else:
                credentials_section += f"""
   • Password: {password}
   
⚠️  IMPORTANT SECURITY NOTICE:
   Please log in and change your password for security reasons.
   Your account access may be limited until you update your password."""
        else:
            credentials_section += f"""
   • Password: Set separately by administrator
   
📧 Contact your administrator or support team if you need password assistance."""

        credentials_section += f"""

👥 Account Created By: {created_by.get_full_name() or created_by.username if created_by else 'System Administrator'}
📅 Account Created: {format_ist_time(user.created_at) if user.created_at else 'Today'}

═══════════════════════════════════════════════════════════════
"""
        
        # Create comprehensive welcome email content
        email_subject = f'Welcome to {company_name} - Your RecallIQ Account is Ready!'
        email_body = f'''Dear {user_full_name},

🎉 Welcome to RecallIQ! 

Your account has been successfully created and you now have access to our comprehensive email reminder and management system.

{credentials_section}

🚀 GETTING STARTED - QUICK SETUP GUIDE:

Step 1: Log into your account
   → Visit: {settings.FRONTEND_URL or 'http://localhost:3000'}
   → Use your email and password to sign in

Step 2: Complete your profile
   → Add your contact information
   → Upload your profile picture
   → Set your preferences

Step 3: Configure email settings
   → Set up your email configurations for sending
   → Test your email connectivity
   → Choose your default sender settings

Step 4: Start using RecallIQ
   → Create your first email template
   → Import your contacts or create groups
   → Schedule your first email batch

💼 WHAT YOU CAN DO WITH RECALLIQ:

✅ Email Template Management
   • Create and customize professional email templates
   • Use dynamic variables for personalization
   • Preview emails before sending

✅ Contact & Group Management  
   • Organize contacts into targeted groups
   • Import contacts from Excel/CSV files
   • Manage subscriber lists efficiently

✅ Automated Email Campaigns
   • Schedule email batches for optimal timing
   • Set up automated reminder sequences
   • Track delivery and engagement metrics

✅ Advanced Analytics
   • Monitor email delivery rates
   • Track opens, clicks, and engagement
   • Generate detailed performance reports

✅ Multi-Configuration Support
   • Manage multiple email accounts
   • Switch between different sending configurations
   • Maintain separate settings for different campaigns

📊 YOUR ACCOUNT DETAILS:

Account Type: {user.get_role_display()}
Company: {company_name}
{f"Monthly Email Limit: {tenant.monthly_email_limit:,} emails" if tenant else ""}
{f"Current Usage: {tenant.emails_sent_this_month_countable:,} emails sent this month" if tenant else ""}
{f"Plan Status: {tenant.get_status_display()}" if tenant else ""}

🆘 NEED HELP?

Our support team is here to help you get started:
📧 Email Support: {settings.SUPPORT_EMAIL or 'support@recalliq.com'}
📞 Phone Support: {getattr(settings, 'SUPPORT_PHONE', 'Contact your administrator')}
💬 Live Chat: Available in your dashboard
📚 Documentation: {settings.FRONTEND_URL or 'http://localhost:3000'}/help

🔒 SECURITY & PRIVACY:

Your account security is our top priority:
• All data is encrypted and securely stored
• Regular security updates and monitoring
• GDPR compliant data handling
• Two-factor authentication available

We're excited to have you join the RecallIQ family and look forward to helping you streamline your email communications!

Best regards,
The RecallIQ Team
{company_name}

---
This is an automated welcome message. 
For technical support, please contact: {settings.SUPPORT_EMAIL or 'support@recalliq.com'}
© {timezone.now().year} RecallIQ. All rights reserved.'''

        # Create email log entry BEFORE attempting to send
        try:
            # For users without tenant (like super_admin), try to get a default tenant or create system log
            log_tenant = tenant
            if not log_tenant:
                # Try to find a default tenant for logging purposes
                from tenants.models import Tenant
                log_tenant = Tenant.objects.filter(status='active').first()
                
                # If still no tenant, create a temporary system tenant entry for logging
                if not log_tenant:
                    log_tenant = Tenant.objects.filter(name__icontains='system').first()
                    if not log_tenant:
                        print("Warning: No tenant found for email logging, creating system tenant")
                        log_tenant, created = Tenant.objects.get_or_create(
                            name='System',
                            domain='system.recalliq.com',
                            defaults={
                                'plan': 'enterprise',
                                'status': 'active',
                                'monthly_email_limit': 999999
                            }
                        )
                        if created:
                            print("Created system tenant for email logging")
            
            if log_tenant:
                # Determine if this should count against tenant limits
                # Welcome emails sent by super admin don't count against tenant limits
                counts_against_limit = True
                direction = 'outgoing'  # Default direction
                
                if created_by and created_by.role == 'super_admin':
                    counts_against_limit = False
                    # If super admin is sending to a tenant user, it's incoming for the tenant
                    if user.tenant:
                        direction = 'incoming'
                elif created_by is None and user.tenant:
                    # Self-registration or system-generated welcome emails for tenant users
                    # These should also be incoming for the tenant
                    direction = 'incoming'
                    counts_against_limit = False
                
                email_log = EmailLog.objects.create(
                    tenant=log_tenant,
                    email_type='welcome',
                    status='queued',
                    direction=direction,
                    from_email=from_email,
                    to_email=user.email,
                    subject=email_subject,
                    body=email_body,
                    sent_by_user=created_by,  # Track who created the user (and thus sent welcome email)
                    counts_against_limit=counts_against_limit,  # Super admin emails don't count
                    metadata={
                        'user_id': user.id,
                        'user_role': user.role,
                        'user_tenant_id': tenant.id if tenant else None,
                        'user_tenant_name': tenant.name if tenant else 'No Tenant',
                        'created_by_id': created_by.id if created_by else None,
                        'created_by_name': created_by.get_full_name() or created_by.username if created_by else 'System',
                        'email_config_id': email_config.id if email_config else None,
                        'email_config_name': email_config.name if email_config else 'Default',
                        'email_config_source': email_config_source,
                        'has_temporary_password': bool(password),
                        'company_name': company_name,
                        'is_system_user': not bool(tenant),
                        'django_email_configured': django_email_configured,
                        'used_custom_backend': bool(backend),
                        'counts_against_limit': counts_against_limit
                    }
                )
                print(f"Email log created with ID: {email_log.id} for tenant: {log_tenant.name}")
            else:
                print("Unable to create email log - no tenant available")
                
        except Exception as e:
            print(f"Failed to create email log: {e}")
            import traceback
            traceback.print_exc()
        
        # Test connection if using custom backend
        if backend:
            try:
                print("Testing email connection...")
                connection = backend.open()
                if connection:
                    print("Email connection successful")
                    backend.close()
                else:
                    print("Email connection failed, falling back to Django settings")
                    backend = None
                    if email_log:
                        email_log.error_message = "Email connection failed, using fallback settings"
                        email_log.save()
            except Exception as e:
                print(f"Email connection test failed: {e}, falling back to Django settings")
                backend = None
                if email_log:
                    email_log.error_message = f"Connection test failed: {str(e)}"
                    email_log.save()
        
        # Create and send the welcome email
        try:
            print(f"Creating welcome email from {from_email} to {user.email}")
            print(f"Using backend: {type(backend).__name__ if backend else 'Default Django backend'}")
            
            welcome_email = EmailMessage(
                subject=email_subject,
                body=email_body,
                from_email=from_email,
                to=[user.email],
                connection=backend
            )
            
            # Send the email
            print(f"Attempting to send email...")
            result = welcome_email.send()
            print(f"Email send result: {result}")
            
            if result == 1:
                print(f"Welcome email sent successfully to {user.email}")
                logger.info(f"Welcome email sent successfully to {user.email}")
                
                # Update email log status to sent
                if email_log:
                    email_log.status = 'sent'
                    email_log.sent_at = timezone.now()
                    email_log.save()
                    print(f"Email log updated to 'sent' status")
                else:
                    print("Warning: No email log to update")
                
                return True
            elif result == 0:
                error_msg = "Email send returned 0 - no emails were sent. This could indicate a configuration issue."
                print(f"Welcome email failed to send to {user.email}: {error_msg}")
                
                # Update email log status to failed
                if email_log:
                    email_log.status = 'failed'
                    email_log.error_message = error_msg
                    email_log.save()
                    print(f"Email log updated to 'failed' status with error: {error_msg}")
                
                return False
            else:
                error_msg = f"Email send returned unexpected result: {result}"
                print(f"Welcome email unexpected result for {user.email}: {error_msg}")
                
                # Update email log status to failed
                if email_log:
                    email_log.status = 'failed'
                    email_log.error_message = error_msg
                    email_log.save()
                
                return False
                
        except Exception as e:
            error_msg = f"Exception during email send: {str(e)}"
            print(f"Error creating/sending welcome email to {user.email}: {error_msg}")
            logger.error(f"Error sending welcome email to {user.email}: {error_msg}")
            
            # Print full traceback for debugging
            import traceback
            traceback.print_exc()
            
            # Update email log status to failed
            if email_log:
                email_log.status = 'failed'
                email_log.error_message = error_msg
                email_log.save()
                print(f"Email log updated to 'failed' status with error: {error_msg}")
            else:
                print("Warning: No email log to update with error")
                
            return False
        
    except Exception as e:
        error_msg = f"Unexpected error in send_welcome_email: {str(e)}"
        print(f"Unexpected error in send_welcome_email for {user.email}: {error_msg}")
        logger.error(f"Unexpected error in send_welcome_email for {user.email}: {error_msg}")
        
        # Print full traceback for debugging
        import traceback
        traceback.print_exc()
        
        # Update email log status to failed if it exists
        if email_log:
            email_log.status = 'failed'
            email_log.error_message = error_msg
            email_log.save()
            print(f"Email log updated to 'failed' status with error: {error_msg}")
        else:
            print("Warning: No email log exists to update with unexpected error")
            
        return False


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        user = serializer.save()
        password = self.request.data.get('password')  # Get the password from request data
        # Send welcome email for self-registration (async to not block user creation)
        try:
            send_welcome_email(user, password=password, created_by=None)
        except Exception as e:
            print(f"Welcome email failed for user {user.username}: {e}")
            # Continue user creation even if email fails


class TenantAdminRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = TenantAdminRegistrationSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        user = serializer.save()
        password = self.request.data.get('password')  # Get the password from request data
        # Send welcome email for new tenant admin with tenant details
        try:
            send_welcome_email(user, password=password, created_by=None)
        except Exception as e:
            print(f"Welcome email failed for tenant admin {user.username}: {e}")
            # Continue user creation even if email fails


@api_view(['POST'])
@permission_classes([AllowAny])
def google_oauth_signup(request):
    """
    Handle Google OAuth signup for tenant admin registration
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    from tenants.models import Tenant
    from django.utils import timezone
    from datetime import timedelta
    import json
    
    try:
        google_token = request.data.get('googleToken')
        tenant_data = request.data.get('tenantData')
        
        if not google_token:
            return Response({'error': 'Google token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify Google token first (before checking tenant data)
        try:
            # You need to set GOOGLE_OAUTH_CLIENT_ID in settings
            client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', None)
            if not client_id:
                return Response({'error': 'Google OAuth not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            idinfo = id_token.verify_oauth2_token(google_token, google_requests.Request(), client_id)
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
                
            # Get user info from Google
            google_email = idinfo['email']
            google_first_name = idinfo.get('given_name', '')
            google_last_name = idinfo.get('family_name', '')
            google_full_name = idinfo.get('name', f"{google_first_name} {google_last_name}")
            
        except ValueError:
            return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        existing_user = User.objects.filter(email=google_email).first()
        
        if existing_user:
            # User exists - handle login (tenant_data not required for login)
            # Generate JWT tokens for existing user
            refresh = RefreshToken.for_user(existing_user)
            access_token = refresh.access_token
            
            # Add custom claims
            access_token['role'] = existing_user.role
            if existing_user.tenant:
                access_token['tenant_id'] = existing_user.tenant.id
                access_token['tenant_name'] = existing_user.tenant.name
            
            return Response({
                'access': str(access_token),
                'refresh': str(refresh),
                'user': {
                    'id': existing_user.id,
                    'username': existing_user.username,
                    'email': existing_user.email,
                    'first_name': existing_user.first_name,
                    'last_name': existing_user.last_name,
                    'role': existing_user.role,
                    'tenant_id': existing_user.tenant.id if existing_user.tenant else None,
                    'tenant_name': existing_user.tenant.name if existing_user.tenant else None,
                },
                'message': 'Login successful via Google OAuth'
            }, status=status.HTTP_200_OK)
        
        # User doesn't exist - check if this is a login attempt (no tenant data)
        if not tenant_data:
            return Response({'error': 'The User with this account is not there'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate tenant data
        required_fields = ['company_name', 'company_address', 'contact_person', 'contact_email', 'contact_phone']
        for field in required_fields:
            if not tenant_data.get(field):
                return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if company name already exists
        if Tenant.objects.filter(name=tenant_data['company_name']).exists():
            return Response({'error': 'Company name already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create tenant
        tenant = Tenant.objects.create(
            name=tenant_data['company_name'],
            company_address=tenant_data['company_address'],
            contact_person=tenant_data['contact_person'],
            contact_email=tenant_data['contact_email'],
            contact_phone=tenant_data['contact_phone'],
            status='trial',
            plan='starter',
            trial_end_date=timezone.now() + timedelta(days=14),
            monthly_email_limit=1000,
        )
        
        # Create user with Google info
        username = google_email.split('@')[0]  # Use email prefix as username
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=google_email,
            first_name=google_first_name,
            last_name=google_last_name,
            role='tenant_admin',
            tenant=tenant
        )
        
        # Generate a temporary password for Google OAuth users
        import secrets
        import string
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%') for _ in range(12))
        user.set_password(temp_password)
        user.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Add custom claims
        access_token['role'] = user.role
        access_token['tenant_id'] = user.tenant.id
        access_token['tenant_name'] = user.tenant.name
        
        # Send welcome email with temporary password
        try:
            send_welcome_email(user, password=temp_password, created_by=None)
        except Exception as e:
            print(f"Welcome email failed for Google OAuth user {user.username}: {e}")
        
        # Return user data and tokens
        user_serializer = UserSerializer(user)
        return Response({
            'access': str(access_token),
            'refresh': str(refresh),
            'user': user_serializer.data,
            'message': 'Tenant admin registered successfully via Google OAuth'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def send_email_with_super_admin_config(to_email, subject, message, html_message=None):
    """
    Send email using super admin's email configuration as fallback to Django settings
    """
    from django.core.mail import EmailMessage
    from django.core.mail.backends.smtp import EmailBackend
    from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        print(f"Attempting to send email to: {to_email}")
        logger.info(f"Sending email to {to_email} with subject: {subject}")
        
        # Get email configuration and backend
        backend = None
        from_email = settings.DEFAULT_FROM_EMAIL
        email_config = None
        email_config_source = "Django Settings"
        
        # Check if Django email settings are properly configured
        django_email_configured = bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)
        print(f"Django email settings configured: {django_email_configured}")
        
        try:
            super_admin = User.objects.filter(role='super_admin').first()
            if super_admin:
                email_config = UserEmailConfiguration.objects.filter(
                    user=super_admin, 
                    is_default=True, 
                    is_active=True
                ).first()
                
                if email_config:
                    print(f"Found super admin email config: {email_config.name}")
                    email_config_source = f"Super Admin Config: {email_config.name}"
                    
                    try:
                        password_decrypt = email_config.decrypt_password()
                        
                        if password_decrypt and password_decrypt.strip():
                            print(f"Setting up custom email backend with super admin config")
                            backend = EmailBackend(
                                host=email_config.email_host,
                                port=int(email_config.email_port),
                                username=email_config.email_host_user,
                                password=password_decrypt,
                                use_tls=email_config.email_use_tls,
                                use_ssl=email_config.email_use_ssl,
                                fail_silently=False
                            )
                            from_email = email_config.from_email
                            print(f"Email backend configured with host: {email_config.email_host}:{email_config.email_port}")
                        else:
                            print("Failed to decrypt super admin email password, falling back to Django settings")
                    except Exception as e:
                        print(f"Error setting up super admin email backend: {e}")
                else:
                    print("No default email config found for super admin")
            else:
                print("No super admin found")
        except Exception as e:
            print(f"Error getting super admin email config: {e}")
        
        # Final check for email configuration validity
        if not backend:
            if django_email_configured:
                print("Using Django email settings for SMTP")
                backend = EmailBackend(
                    host=settings.EMAIL_HOST,
                    port=settings.EMAIL_PORT,
                    username=settings.EMAIL_HOST_USER,
                    password=settings.EMAIL_HOST_PASSWORD,
                    use_tls=settings.EMAIL_USE_TLS,
                    use_ssl=settings.EMAIL_USE_SSL,
                    fail_silently=False
                )
                from_email = settings.EMAIL_HOST_USER
                email_config_source += " - USING DJANGO SMTP SETTINGS"
            else:
                print("WARNING: No valid email configuration found - using console backend")
                backend = ConsoleEmailBackend()
                email_config_source += " - USING CONSOLE BACKEND"
        
        print(f"Email configuration source: {email_config_source}")
        
        # Create and send email
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=[to_email],
            connection=backend
        )
        
        if html_message:
            email.content_subtype = "html"
            email.body = html_message
        
        result = email.send()
        
        if result:
            print(f"✅ Email sent successfully to {to_email}")
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            print(f"❌ Failed to send email to {to_email}")
            logger.error(f"Failed to send email to {to_email}")
            return False
            
    except Exception as e:
        print(f"❌ Exception sending email to {to_email}: {e}")
        logger.error(f"Exception sending email to {to_email}: {e}")
        return False


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Request password reset by username or email
    """
    print(f"🔍 Password reset request received for: {request.data}")
    
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        username_or_email = serializer.validated_data['username_or_email']
        print(f"🔍 Looking for user with: {username_or_email}")
        
        # Find the user
        user = None
        if '@' in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
                print(f"✅ Found user by email: {user.username}")
            except User.DoesNotExist:
                print(f"❌ No user found with email: {username_or_email}")
                pass
        
        if not user:
            try:
                user = User.objects.get(username=username_or_email)
                print(f"✅ Found user by username: {user.username}")
            except User.DoesNotExist:
                print(f"❌ No user found with username: {username_or_email}")
                pass
        
        if user:
            # Generate reset token
            from .models import PasswordResetToken
            
            # Invalidate old tokens
            PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Create new token
            token = str(uuid.uuid4())
            reset_token = PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            
            # Send reset email
            try:
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
                reset_link = f"{frontend_url}/reset-password?token={token}"
                subject = '🔐 Password Reset Request - RecallIQ'
                
                # Create a professional and appealing email message
                user_display_name = user.first_name or user.username
                formatted_time = format_ist_time()  # Current time in IST
                
                message = f"""
Hello {user_display_name},

We received a request to reset the password for your RecallIQ account. If you made this request, please follow the instructions below to reset your password.

╔══════════════════════════════════════════════════════════════╗
║                    🔐 PASSWORD RESET REQUEST                 ║
╚══════════════════════════════════════════════════════════════╝

📋 ACCOUNT INFORMATION:
   • Full Name: {user.get_full_name() or user_display_name}
   • Username: {user.username}
   • Email Address: {user.email}
   • Request Time: {formatted_time}
   • Account Status: Active

🔗 RESET YOUR PASSWORD:
   Click the secure link below to create a new password:
   
   👉 {reset_link}
   
   Or copy and paste the link into your browser if the above doesn't work.

⏰ IMPORTANT TIMING INFORMATION:
   • This reset link is valid for 24 hours only
   • After 24 hours, you'll need to request a new reset link
   • The link can only be used once for security

🛡️ SECURITY REMINDERS:
   ✅ Only use this link if you requested the password reset
   ✅ Never share this link with anyone else
   ✅ RecallIQ will never ask for your password via email
   ✅ If you didn't request this reset, you can safely ignore this email

❓ DIDN'T REQUEST THIS RESET?
   If you didn't request a password reset, your account is still secure. 
   Someone may have entered your email address by mistake. You can safely 
   ignore this email - no changes will be made to your account.

🆘 NEED ASSISTANCE?
   Our support team is here to help you:
   
   📧 Email Support: {getattr(settings, 'SUPPORT_EMAIL', 'support@recalliq.com')}
   💬 Help Center: {frontend_url}/help
   📞 Phone Support: Available in your dashboard
   
   For security reasons, we cannot reset passwords over the phone or email.

Thank you for using RecallIQ to manage your email campaigns and reminders!

Best regards,
The RecallIQ Security Team

╔══════════════════════════════════════════════════════════════╗
║  This is an automated security message from RecallIQ         ║
║  Please do not reply to this email                          ║
║  © 2025 RecallIQ Platform - All Rights Reserved             ║
╚══════════════════════════════════════════════════════════════╝

P.S. Keep your account secure by using a strong, unique password and 
enabling two-factor authentication when available.
"""
                
                # Use the new helper function to send email with super admin config
                email_sent = send_email_with_super_admin_config(
                    to_email=user.email,
                    subject=subject,
                    message=message
                )
                
                if email_sent:
                    print(f"✅ Password reset email sent successfully to {user.email}")
                else:
                    print(f"❌ Failed to send password reset email to {user.email}")
                
            except Exception as e:
                print(f"❌ Exception sending password reset email: {e}")
                import traceback
                traceback.print_exc()
        
        # Always return success to prevent email enumeration
        return Response({'message': 'If a user with that username or email exists, a password reset link has been sent.'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Confirm password reset with token
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            from .models import PasswordResetToken
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if not reset_token.is_valid():
                return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Reset password
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            return Response({'message': 'Password reset successful'})
            
        except PasswordResetToken.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_signup_otp(request):
    """
    Request OTP for email verification during signup
    """
    serializer = EmailOTPRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        # Generate 6-digit OTP
        import random
        otp = str(random.randint(100000, 999999))
        
        # Store OTP and signup data
        from django.utils import timezone
        from datetime import timedelta
        from .models import EmailOTPVerification
        
        # Invalidate old OTPs for this email
        EmailOTPVerification.objects.filter(email=email, is_used=False).update(is_used=True)
        
        # Create new OTP
        otp_verification = EmailOTPVerification.objects.create(
            email=email,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10),
            signup_data=serializer.validated_data
        )
        
        # Send OTP email
        try:
            subject = '📧 Email Verification Code - RecallIQ'
            formatted_time = format_ist_time()
            
            message = f"""
Hello,

Welcome to RecallIQ! Please verify your email address to complete your registration.

╔══════════════════════════════════════════════════════════════╗
║                 📧 EMAIL VERIFICATION CODE                   ║
╚══════════════════════════════════════════════════════════════╝

🔢 YOUR VERIFICATION CODE:

    {otp}

📋 VERIFICATION DETAILS:
   • Email Address: {email}
   • Generated Time: {formatted_time}
   • Valid For: 10 minutes only
   • One-time Use: This code can only be used once

⏰ IMPORTANT TIMING:
   ⚠️  This verification code will expire in 10 minutes for your security.
   ⚠️  If the code expires, you'll need to request a new one.

🔐 SECURITY NOTICE:
   • Enter this code on the RecallIQ registration page only
   • Never share this code with anyone
   • RecallIQ support will never ask for this code
   • If you didn't request this code, please ignore this email

🆘 NEED HELP?
   If you're having trouble with verification:
   📧 Contact Support: {getattr(settings, 'SUPPORT_EMAIL', 'support@recalliq.com')}
   💬 Help Center: {getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/help

Thank you for choosing RecallIQ for your email campaign needs!

Best regards,
The RecallIQ Team

╔══════════════════════════════════════════════════════════════╗
║  This is an automated verification message from RecallIQ     ║
║  Please do not reply to this email                          ║
║  © 2025 RecallIQ Platform - All Rights Reserved             ║
╚══════════════════════════════════════════════════════════════╝
"""
            
            # Use super admin email configuration
            email_sent = send_email_with_super_admin_config(
                to_email=email,
                subject=subject,
                message=message
            )
            
            if email_sent:
                return Response({
                    'message': 'OTP sent to your email',
                    'email': email
                })
            else:
                return Response({
                    'error': 'Failed to send OTP email'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            print(f"Failed to send OTP email: {e}")
            return Response({'error': 'Failed to send OTP email'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_signup_otp(request):
    """
    Verify OTP and complete signup
    """
    serializer = EmailOTPVerifySerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        
        try:
            from .models import EmailOTPVerification
            otp_verification = EmailOTPVerification.objects.get(
                email=email, 
                otp=otp, 
                is_used=False
            )
            
            # Increment attempts
            otp_verification.attempts += 1
            otp_verification.save()
            
            if not otp_verification.is_valid():
                if otp_verification.attempts >= 3:
                    return Response({'error': 'Too many invalid attempts. Please request a new OTP.'}, status=status.HTTP_400_BAD_REQUEST)
                elif otp_verification.is_expired():
                    return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create user and tenant from stored signup data
            signup_data = otp_verification.signup_data
            
            # Create tenant
            from django.utils import timezone
            from datetime import timedelta
            from tenants.models import Tenant
            
            tenant_data = {
                'name': signup_data['company_name'],
                'company_address': signup_data['company_address'],
                'contact_person': signup_data['contact_person'],
                'contact_email': signup_data['contact_email'],
                'contact_phone': signup_data['contact_phone'],
                'status': 'trial',
                'plan': 'starter',
                'trial_end_date': timezone.now() + timedelta(days=14),
                'monthly_email_limit': 1000,
            }
            
            tenant = Tenant.objects.create(**tenant_data)
            
            # Create user
            user_data = {
                'username': signup_data['username'],
                'email': signup_data['email'],
                'first_name': signup_data['first_name'],
                'last_name': signup_data['last_name'],
                'role': 'tenant_admin',
                'tenant': tenant
            }
            
            user = User.objects.create_user(**user_data)
            signup_password = signup_data['password']  # Get the password from signup data
            user.set_password(signup_password)
            user.save()
            
            # Mark OTP as used
            otp_verification.is_used = True
            otp_verification.save()
            
            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Add custom claims
            access_token['role'] = user.role
            access_token['tenant_id'] = user.tenant.id
            access_token['tenant_name'] = user.tenant.name
            
            # Send welcome email with the password
            try:
                send_welcome_email(user, password=signup_password, created_by=None)
            except Exception as e:
                print(f"Welcome email failed for user {user.username}: {e}")
            
            # Return user data and tokens
            user_serializer = UserSerializer(user)
            return Response({
                'success': True,
                'access': str(access_token),
                'refresh': str(refresh),
                'user': user_serializer.data,
                'message': 'Registration completed successfully'
            }, status=status.HTTP_201_CREATED)
            
        except EmailOTPVerification.DoesNotExist:
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserProfileUpdateSerializer
        return UserSerializer
    
    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            print(f"Profile update error: {e}")
            print(f"Request data: {request.data}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_update(self, serializer):
        """Override to track who made the changes for notifications"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Store the user who made the change for notification purposes
        instance = serializer.instance
        instance._changed_by = self.request.user
        
        logger.info(f"🔧 perform_update called for user profile {instance.username} by {self.request.user.username}")
        logger.info(f"🔧 Setting _changed_by to: {instance._changed_by}")
        
        result = serializer.save()
        
        logger.info(f"🔧 serializer.save() completed for user profile update")
        return result


class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdminOrSupportTeamNonDestructive]
    
    def get_permissions(self):
        """Allow super_admin, support_team, tenant_admin with proper permissions"""
        if self.request.method == 'POST':
            # For creating users, allow super_admin, support_team, and tenant_admin
            return [IsTenantAdmin()]
        
        # For GET requests, allow broader access
        return [IsTenantAdmin()]
    
    def get_queryset(self):
        """Return users based on role and access permissions with filtering"""
        user = self.request.user
        
        print(f"[DEBUG] UserListView.get_queryset() called for user: {user.username} (role: {user.role})")
        
        if user.role in ['super_admin', 'support_team']:
            # Super admin and Support team see ALL users in the system
            queryset = User.objects.all().select_related('tenant', 'created_by').order_by('-created_at')
            
            # Apply filters for super admin
            tenant_filter = self.request.query_params.get('tenant', None)
            role_filter = self.request.query_params.get('role', None)
            search_query = self.request.query_params.get('search', None)
            created_by_filter = self.request.query_params.get('created_by', None)
            
            print(f"[DEBUG] Filters: tenant={tenant_filter}, role={role_filter}, search={search_query}, created_by={created_by_filter}")
            
            if tenant_filter:
                if tenant_filter == 'null':
                    queryset = queryset.filter(tenant__isnull=True)
                else:
                    queryset = queryset.filter(tenant_id=tenant_filter)
            
            if role_filter:
                queryset = queryset.filter(role=role_filter)
            
            if created_by_filter:
                queryset = queryset.filter(created_by_id=created_by_filter)
            
            if search_query:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(username__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query)
                )
            
            print(f"[DEBUG] Super admin query with filters - returning {queryset.count()} users")
            return queryset
            
        elif user.role in ['tenant_admin', 'staff_admin', 'sales_team']:
            # Tenant admin, staff admin, and sales team see all users in their tenant
            queryset = User.objects.filter(
                tenant=user.tenant
            ).select_related('tenant', 'created_by').order_by('-created_at')
            
            # Apply basic filters for tenant admin
            role_filter = self.request.query_params.get('role', None)
            search_query = self.request.query_params.get('search', None)
            
            if role_filter:
                queryset = queryset.filter(role=role_filter)
            
            if search_query:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(username__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query)
                )
            
            print(f"[DEBUG] Tenant admin query with filters - returning {queryset.count()} users")
            return queryset
        
        # Other roles see only themselves
        queryset = User.objects.filter(id=user.id)
        print(f"[DEBUG] Other role query - returning {queryset.count()} users")
        return queryset
    
    def get_serializer_context(self):
        """Add request user to serializer context for validation"""
        context = super().get_serializer_context()
        context['request_user'] = self.request.user
        return context
    
    def perform_create(self, serializer):
        # The serializer will handle setting created_by and role validation
        user = serializer.save()
        password = self.request.data.get('password')
        if password:
            user.set_password(password)
            user.save()
            
        # Send welcome email with temporary password (async to not block user creation)
        try:
            send_welcome_email(user, password=password, created_by=self.request.user)
        except Exception as e:
            print(f"Welcome email failed for user {user.username}: {e}")
            # Continue user creation even if email fails


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdminOrSupportTeamNonDestructive]
    
    def get_permissions(self):
        """Allow different access based on user role - support_team cannot delete"""
        if self.request.method == 'DELETE':
            # Only super admin can delete users
            return [IsSuperAdmin()]
        
        # For GET/PUT requests, support_team has same access as super_admin
        return [IsTenantAdmin()]
    
    def get_queryset(self):
        """Return users based on role and access permissions"""
        user = self.request.user
        
        if user.role in ['super_admin', 'support_team']:
            # Super admin and Support team see ALL users in the system
            return User.objects.all()
        elif user.role in ['tenant_admin', 'staff_admin', 'sales_team']:
            # Tenant admin, staff admin, and sales team see all users in their tenant
            return User.objects.filter(
                tenant=user.tenant
            )
        
        # Other roles see only themselves
        return User.objects.filter(id=user.id)
    
    def get_serializer_context(self):
        """Add request user to serializer context for validation"""
        context = super().get_serializer_context()
        context['request_user'] = self.request.user
        return context
    
    def perform_update(self, serializer):
        """Override to track who made the changes for notifications"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Store the user who made the change for notification purposes
        instance = serializer.instance
        instance._changed_by = self.request.user
        
        logger.info(f"🔧 perform_update called for user {instance.username} by {self.request.user.username}")
        logger.info(f"🔧 Setting _changed_by to: {instance._changed_by}")
        
        result = serializer.save()
        
        logger.info(f"🔧 serializer.save() completed for user update")
        return result
    
    def perform_destroy(self, instance):
        """Override to add deletion restrictions for tenant admins"""
        user = self.request.user
        
        # Tenant admin cannot delete users created by super admin
        if (user.role == 'tenant_admin' and 
            instance.created_by and 
            instance.created_by.role == 'super_admin'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You cannot delete users created by super admin")
        
        # Tenant admin created by another tenant admin cannot delete ANY users
        if (user.role == 'tenant_admin' and 
            user.created_by and 
            user.created_by.role == 'tenant_admin'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Tenant admin created by another tenant admin cannot delete users")
        
        # Staff admin cannot delete ANY users
        if user.role == 'staff_admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Staff admin cannot delete users")
        
        # Tenant admin can only delete users in their own tenant
        if (user.role == 'tenant_admin' and 
            instance.tenant != user.tenant):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete users in your own tenant")
        
        # Prevent tenant admin from deleting themselves
        if user.role == 'tenant_admin' and instance.id == user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You cannot delete your own account")
        
        super().perform_destroy(instance)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response({'error': 'Current password and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not user.check_password(current_password):
        return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(new_password) < 8:
        return Response({'error': 'New password must be at least 8 characters long'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()
    
    return Response({'message': 'Password changed successfully'})


class UserEmailConfigurationViewSet(generics.ListCreateAPIView):
    serializer_class = UserEmailConfigurationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # All users see only their own email configurations
        return UserEmailConfiguration.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Always create configurations for the current user
        serializer.save(user=self.request.user)


class UserEmailConfigurationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserEmailConfigurationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # All users see only their own email configurations
        return UserEmailConfiguration.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            print(f"Email configuration update error: {e}")
            print(f"Request data: {request.data}")
            return Response({
                'error': str(e),
                'detail': 'Failed to update email configuration'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_email_configuration(request, config_id):
    try:
        config = UserEmailConfiguration.objects.get(id=config_id, user=request.user)
        
        # Validate user has email
        if not request.user.email:
            return Response({'error': 'User email is not set. Please set your email address in profile.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate configuration has required fields
        if not config.email_host or not config.email_host_user or not config.from_email:
            return Response({'error': 'Email configuration is incomplete. Missing host, username, or from email.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if password exists in encrypted form
        if not config.encrypted_email_host_password:
            return Response({'error': 'Email password is not set. Please update your configuration with a password.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get decrypted password with error handling
        try:
            password = config.decrypt_password()
            if not password or password.strip() == '':
                return Response({'error': 'Email password could not be decrypted or is empty. Please update your configuration.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Failed to decrypt password: {str(e)}. Please update your configuration.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Import required modules for email sending
        from django.core.mail import EmailMessage
        from django.core.mail.backends.smtp import EmailBackend
        import smtplib
        
        # Test SMTP connection first
        try:
            # Create a custom backend with the configuration settings
            backend = EmailBackend(
                host=config.email_host,
                port=int(config.email_port),
                username=config.email_host_user,
                password=password,
                use_tls=config.email_use_tls,
                use_ssl=config.email_use_ssl,
                fail_silently=False
            )
            
            # Test connection by opening and closing
            connection = backend.open()
            if not connection:
                return Response({'error': 'Failed to establish SMTP connection. Please check your settings.'}, status=status.HTTP_400_BAD_REQUEST)
            backend.close()
            
        except Exception as e:
            return Response({'error': f'SMTP connection failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create and send test email
        try:
            test_email = EmailMessage(
                subject='RecallIQ - Email Configuration Test',
                body=f'''Hello {request.user.first_name or request.user.username},

This is a test email from RecallIQ to verify your email configuration is working correctly.

Configuration Details:
- Name: {config.name}
- Provider: {config.get_provider_display()}
- From Email: {config.from_email}
- SMTP Host: {config.email_host}
- Port: {config.email_port}
- Encryption: {'TLS' if config.email_use_tls else 'SSL' if config.email_use_ssl else 'None'}

If you received this email, your email configuration is working properly!

Best regards,
RecallIQ Team''',
                from_email=config.from_email,
                to=[request.user.email],
                connection=backend
            )
            
            # Send the test email
            result = test_email.send()
            if result == 1:
                return Response({'message': 'Test email sent successfully! Check your inbox.'})
            else:
                return Response({'error': 'Email was not sent. Please check your configuration.'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'error': f'Failed to send test email: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
    except UserEmailConfiguration.DoesNotExist:
        return Response({'error': 'Email configuration not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Unexpected error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_email_settings(request):
    """Test email settings without saving configuration"""
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['email_host', 'email_port', 'email_host_user', 'email_host_password', 'from_email']
        for field in required_fields:
            if not data.get(field):
                return Response({'error': f'Missing required field: {field}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate user has email
        if not request.user.email:
            return Response({'error': 'User email is not set. Please set your email address in profile.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Import required modules for email sending
        from django.core.mail import EmailMessage
        from django.core.mail.backends.smtp import EmailBackend
        
        # Test SMTP connection first
        try:
            backend = EmailBackend(
                host=data['email_host'],
                port=int(data['email_port']),
                username=data['email_host_user'],
                password=data['email_host_password'],
                use_tls=data.get('email_use_tls', False),
                use_ssl=data.get('email_use_ssl', False),
                fail_silently=False
            )
            
            # Test connection
            connection = backend.open()
            if not connection:
                return Response({'error': 'Failed to establish SMTP connection. Please check your settings.'}, status=status.HTTP_400_BAD_REQUEST)
            backend.close()
            
        except Exception as e:
            return Response({'error': f'SMTP connection failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Send test email
        try:
            test_email = EmailMessage(
                subject='RecallIQ - Email Settings Test',
                body=f'''Hello {request.user.first_name or request.user.username},

This is a test email to verify your email settings are working correctly.

Settings tested:
- SMTP Host: {data['email_host']}
- Port: {data['email_port']}
- From Email: {data['from_email']}
- Encryption: {'TLS' if data.get('email_use_tls') else 'SSL' if data.get('email_use_ssl') else 'None'}

If you received this email, your email settings are working properly!

Best regards,
RecallIQ Team''',
                from_email=data['from_email'],
                to=[request.user.email],
                connection=backend
            )
            
            result = test_email.send()
            if result == 1:
                return Response({'message': 'Test email sent successfully! Check your inbox.'})
            else:
                return Response({'error': 'Email was not sent. Please check your settings.'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'error': f'Failed to send test email: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({'error': f'Unexpected error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_default_email_configuration(request):
    try:
        config = UserEmailConfiguration.objects.get(user=request.user, is_default=True, is_active=True)
        serializer = UserEmailConfigurationSerializer(config)
        return Response(serializer.data)
    except UserEmailConfiguration.DoesNotExist:
        return Response({'error': 'No default email configuration found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    user = request.user
    
    # Safe access to tenant information
    tenant_id = None
    tenant_name = None
    if hasattr(user, 'tenant') and user.tenant:
        tenant_id = user.tenant.id
        tenant_name = user.tenant.name
    
    # For super admin and support team, use comprehensive dashboard
    if user.role in ['super_admin', 'support_team']:
        from .dashboard_views import _get_super_admin_dashboard
        comprehensive_data = _get_super_admin_dashboard()
        
        # Add user and permission info to comprehensive dashboard
        comprehensive_data.update({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'tenant_id': tenant_id,
                'created_at': user.created_at,
            },
            'tenant': tenant_name,
            'role': user.role,
            'permissions': {
                'is_super_admin': user.role == 'super_admin',
                'is_tenant_admin': user.role in ['super_admin', 'tenant_admin', 'staff_admin'],
                'can_manage_users': user.role in ['super_admin', 'tenant_admin', 'staff_admin'],
                'can_manage_templates': user.role in ['super_admin', 'tenant_admin', 'staff_admin', 'staff'],
                'can_manage_batches': user.role in ['super_admin', 'tenant_admin', 'staff_admin', 'staff'],
            }
        })
        return Response(comprehensive_data)
    
    # For tenant users, return basic dashboard
    dashboard_data = {
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'tenant_id': tenant_id,
            'created_at': user.created_at,
        },
        'tenant': tenant_name,
        'role': user.role,
        'permissions': {
            'is_super_admin': user.role == 'super_admin',
            'is_tenant_admin': user.role in ['super_admin', 'tenant_admin', 'staff_admin'],
            'can_manage_users': user.role in ['super_admin', 'tenant_admin', 'staff_admin'],
            'can_manage_templates': user.role in ['super_admin', 'tenant_admin', 'staff_admin', 'staff'],
            'can_manage_batches': user.role in ['super_admin', 'tenant_admin', 'staff_admin', 'staff'],
        }
    }
    
    return Response(dashboard_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def debug_welcome_email(request):
    """Debug endpoint to test welcome email functionality"""
    if request.user.role != 'super_admin':
        return Response({'error': 'Only super admin can use this debug endpoint'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Test with current user
        user = request.user
        result = send_welcome_email(user, password='TestPassword123', created_by=user)
        
        return Response({
            'message': 'Debug welcome email test completed',
            'result': result,
            'user_email': user.email,
            'user_tenant': user.tenant.name if user.tenant else None
        })
    except Exception as e:
        import traceback
        return Response({
            'error': f'Debug email test failed: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_user_visibility(request):
    """Debug endpoint to check user visibility issues"""
    try:
        user = request.user
        
        # Get all users
        all_users = User.objects.all()
        
        # Get users this user should see based on role
        if user.role == 'super_admin':
            visible_users = User.objects.all()
        elif user.role in ['tenant_admin', 'staff_admin']:
            visible_users = User.objects.filter(created_by=user, tenant=user.tenant)
        else:
            visible_users = User.objects.filter(id=user.id)
        
        return Response({
            'current_user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'tenant': user.tenant.name if user.tenant else None
            },
            'all_users_count': all_users.count(),
            'all_users': [
                {
                    'id': u.id,
                    'username': u.username,
                    'role': u.role,
                    'created_by': u.created_by.username if u.created_by else None,
                    'tenant': u.tenant.name if u.tenant else None
                }
                for u in all_users
            ],
            'visible_users_count': visible_users.count(),
            'visible_users': [
                {
                    'id': u.id,
                    'username': u.username,
                    'role': u.role,
                    'created_by': u.created_by.username if u.created_by else None,
                    'tenant': u.tenant.name if u.tenant else None
                }
                for u in visible_users
            ],
            'filter_logic': f"Role: {user.role}, Filter: ALL USERS" if user.role == 'super_admin' else f"Role: {user.role}, Filter: created_by={user.id} AND tenant={user.tenant_id if user.tenant else None}"
        })
    except Exception as e:
        import traceback
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fix_email_config_password(request):
    """Fix email configuration password encryption"""
    if request.user.role != 'super_admin':
        return Response({'error': 'Only super admin can use this endpoint'}, status=status.HTTP_403_FORBIDDEN)
    
    config_id = request.data.get('config_id')
    new_password = request.data.get('password')
    
    if not config_id or not new_password:
        return Response({'error': 'config_id and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        email_config = UserEmailConfiguration.objects.get(id=config_id, user=request.user)
        
        # Re-encrypt the password
        email_config.encrypt_password(new_password)
        email_config.save()
        
        # Test decryption
        decrypted = email_config.decrypt_password()
        
        return Response({
            'message': 'Email configuration password updated successfully',
            'config_name': email_config.name,
            'encryption_test': 'Success' if decrypted == new_password else 'Failed',
            'encrypted_length': len(email_config.encrypted_email_host_password)
        })
    except UserEmailConfiguration.DoesNotExist:
        return Response({'error': 'Email configuration not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        return Response({
            'error': f'Failed to fix email configuration: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_user_roles(request):
    """Get available user roles based on the requesting user's permissions"""
    user = request.user
    
    if user.role in ['super_admin', 'support_team']:
        # Super admin and support team can create all user roles
        available_roles = [
            {'value': 'tenant_admin', 'label': 'Tenant Admin'},
            {'value': 'sales_team', 'label': 'Sales Team'},
            {'value': 'support_team', 'label': 'Support Team'},
            {'value': 'staff_admin', 'label': 'Staff Admin'},
            {'value': 'staff', 'label': 'Staff'}
        ]
    elif user.role in ['tenant_admin', 'staff_admin']:
        # Tenant admin and staff admin can create staff_admin and staff users (but NOT tenant_admin or user role)
        available_roles = [
            {'value': 'staff_admin', 'label': 'Staff Admin'},
            {'value': 'staff', 'label': 'Staff'}
        ]
    else:
        # Other roles cannot create users
        available_roles = []
    
    return Response({
        'available_roles': available_roles,
        'can_create_users': len(available_roles) > 0,
        'requesting_user_role': user.role
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_filter_options(request):
    """Get available filter options for user management"""
    try:
        user = request.user
        
        # Only super admin, Support team, tenant admin, and staff admin can access this
        if user.role not in ['super_admin', 'support_team', 'tenant_admin', 'staff_admin']:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        filter_options = {
            'roles': [],
            'tenants': [],
            'creators': []
        }
        
        if user.role in ['super_admin', 'support_team']:
            # Super admin and Support team can filter by all tenants and creators
            from tenants.models import Tenant
            
            tenants = Tenant.objects.all().order_by('name')
            filter_options['tenants'] = [
                {'value': 'null', 'label': 'No Tenant (System Users)'}
            ] + [
                {'value': tenant.id, 'label': tenant.name}
                for tenant in tenants
            ]
            
            # Get all users who have created other users
            creators = User.objects.filter(
                created_users__isnull=False
            ).distinct().order_by('username')
            
            filter_options['creators'] = [
                {'value': creator.id, 'label': f"{creator.get_full_name() or creator.username} ({creator.role})"}
                for creator in creators
            ]
            
            # Add all role options for super admin and Support team
            filter_options['roles'] = [
                {'value': 'super_admin', 'label': 'Super Admin'},
                {'value': 'support_team', 'label': 'Support team'},
                {'value': 'sales_team', 'label': 'Sales Team'},
                {'value': 'tenant_admin', 'label': 'Tenant Admin'},
                {'value': 'staff_admin', 'label': 'Staff Admin'},
                {'value': 'staff', 'label': 'Staff'},
                {'value': 'user', 'label': 'User'},
            ]
        
        elif user.role in ['tenant_admin', 'staff_admin']:
            # Tenant admin and staff admin only see their own tenant and themselves as creator
            filter_options['tenants'] = [
                {'value': user.tenant.id, 'label': f"{user.tenant.name} (Your Tenant)"}
            ] if user.tenant else []
            
            filter_options['creators'] = [
                {'value': user.id, 'label': f"{user.get_full_name() or user.username} (You)"}
            ]
            
            # Both can filter staff roles, tenant admin can also see staff_admin
            if user.role == 'tenant_admin':
                filter_options['roles'] = [
                    {'value': 'staff_admin', 'label': 'Staff Admin'},
                    {'value': 'staff', 'label': 'Staff'},
                ]
            else:  # staff_admin
                filter_options['roles'] = [
                    {'value': 'staff', 'label': 'Staff'},
                ]
        
        return Response(filter_options)
        
    except Exception as e:
        import traceback
        return Response({
            'error': f'Failed to get filter options: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_email_config_health(request):
    """Check the health of all email configurations for current user"""
    try:
        configs = UserEmailConfiguration.objects.filter(user=request.user)
        config_status = []
        
        for config in configs:
            status_info = {
                'id': config.id,
                'name': config.name,
                'from_email': config.from_email,
                'is_active': config.is_active,
                'is_default': config.is_default,
                'created_at': config.created_at,
                'has_encrypted_password': bool(config.encrypted_email_host_password),
                'encrypted_data_length': len(config.encrypted_email_host_password) if config.encrypted_email_host_password else 0,
            }
            
            # Test password decryption
            try:
                decrypted = config.decrypt_password()
                status_info['password_status'] = 'working' if decrypted else 'failed'
                status_info['can_decrypt'] = bool(decrypted)
                if decrypted:
                    status_info['password_length'] = len(decrypted)
            except Exception as e:
                status_info['password_status'] = 'error'
                status_info['can_decrypt'] = False
                status_info['password_error'] = str(e)
            
            config_status.append(status_info)
        
        # Check system encryption key status
        encryption_key_status = 'missing'
        if hasattr(settings, 'ENCRYPTION_KEY') and settings.ENCRYPTION_KEY:
            try:
                from cryptography.fernet import Fernet
                Fernet(settings.ENCRYPTION_KEY.encode())
                encryption_key_status = 'valid'
            except:
                encryption_key_status = 'invalid'
        
        # Summary
        total_configs = len(config_status)
        working_configs = len([c for c in config_status if c.get('password_status') == 'working'])
        broken_configs = total_configs - working_configs
        
        return Response({
            'encryption_key_status': encryption_key_status,
            'summary': {
                'total_configurations': total_configs,
                'working_configurations': working_configs,
                'broken_configurations': broken_configs,
                'health_percentage': (working_configs / total_configs * 100) if total_configs > 0 else 100
            },
            'configurations': config_status,
            'recommendations': [
                'Re-enter passwords for configurations with password_status: "failed" or "error"',
                'Contact system administrator if encryption_key_status is not "valid"',
                'Test email sending after fixing any broken configurations'
            ] if broken_configs > 0 else ['All email configurations are healthy']
        })
        
    except Exception as e:
        import traceback
        return Response({
            'error': f'Failed to check email configuration health: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tenant_email_configurations(request):
    """
    Get email configurations for the user's tenant.
    Staff Admin and Staff can use this to access their tenant's email configurations for batches.
    """
    user = request.user
    
    # Only allow staff_admin and staff users to access this endpoint
    if user.role not in ['staff_admin', 'staff']:
        return Response({
            'error': 'This endpoint is only available for staff admin and staff users'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if user belongs to a tenant
    if not user.tenant:
        return Response({
            'error': 'User is not associated with any tenant'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get email configurations from tenant admin users in the same tenant
        tenant_admin_users = User.objects.filter(
            tenant=user.tenant,
            role='tenant_admin'
        )
        
        if not tenant_admin_users.exists():
            return Response({
                'results': [],
                'message': 'No tenant admin found to provide email configurations'
            })
        
        # Get active email configurations from all tenant admins in this tenant
        email_configs = UserEmailConfiguration.objects.filter(
            user__in=tenant_admin_users,
            is_active=True
        ).select_related('user')
        
        serializer = UserEmailConfigurationSerializer(email_configs, many=True)
        
        # Return configurations in the same format as the regular endpoint
        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch tenant email configurations: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 🏥 HEALTH MONITORING FUNCTIONALITY - MERGED FROM health_views.py
# =============================================================================

import time
import psutil
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.core.mail import send_mail
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from celery import current_app as celery_app
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import redis


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Basic health check endpoint
    Returns simple OK status for load balancers
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'RecallIQ',
        'version': '2.0.0'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def detailed_health_check(request):
    """
    Comprehensive health check with all system components
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'RecallIQ',
        'version': '2.0.0',
        'checks': {}
    }
    
    # Database health
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database error: {str(e)}'
        }
        health_status['status'] = 'unhealthy'
    
    # Cache health
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test_value', 30)
        if cache.get(cache_key) == 'test_value':
            cache.delete(cache_key)
            health_status['checks']['cache'] = {
                'status': 'healthy',
                'message': 'Cache working properly'
            }
        else:
            health_status['checks']['cache'] = {
                'status': 'unhealthy',
                'message': 'Cache read/write failed'
            }
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'message': f'Cache error: {str(e)}'
        }
        health_status['status'] = 'degraded'
    
    # Celery health
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            health_status['checks']['celery'] = {
                'status': 'healthy',
                'message': f'Celery workers active: {len(stats)}',
                'workers': list(stats.keys())
            }
        else:
            health_status['checks']['celery'] = {
                'status': 'unhealthy',
                'message': 'No Celery workers found'
            }
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['celery'] = {
            'status': 'unhealthy',
            'message': f'Celery error: {str(e)}'
        }
        health_status['status'] = 'degraded'
    
    return Response(health_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def system_metrics(request):
    """
    Get system performance metrics
    """
    try:
        # CPU and Memory metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            'timestamp': time.time(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                }
            },
            'application': {
                'database_connections': len(connection.queries),
                'active_users': User.objects.filter(is_active=True).count(),
                'total_batches': 0,  # Will be filled if batches app is available
                'pending_emails': 0  # Will be filled if logs app is available
            }
        }
        
        # Try to get application-specific metrics
        try:
            from batches.models import Batch
            metrics['application']['total_batches'] = Batch.objects.count()
            metrics['application']['active_batches'] = Batch.objects.filter(status='running').count()
        except ImportError:
            pass
        
        try:
            from logs.models import EmailLog
            metrics['application']['pending_emails'] = EmailLog.objects.filter(status='pending').count()
            metrics['application']['failed_emails'] = EmailLog.objects.filter(status='failed').count()
        except ImportError:
            pass
        
        return Response(metrics)
        
    except Exception as e:
        return Response({
            'error': f'Failed to collect system metrics: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def database_health(request):
    """
    Detailed database health check
    """
    try:
        db_health = {
            'status': 'healthy',
            'timestamp': time.time(),
            'checks': []
        }
        
        # Test basic connectivity
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        connection_time = (time.time() - start_time) * 1000
        
        db_health['checks'].append({
            'test': 'connectivity',
            'status': 'pass',
            'response_time_ms': round(connection_time, 2)
        })
        
        # Test table access
        try:
            User.objects.count()
            db_health['checks'].append({
                'test': 'user_table_access',
                'status': 'pass'
            })
        except Exception as e:
            db_health['checks'].append({
                'test': 'user_table_access',
                'status': 'fail',
                'error': str(e)
            })
            db_health['status'] = 'unhealthy'
        
        # Check migration status
        try:
            from django.core.management import execute_from_command_line
            from io import StringIO
            import sys
            
            # Capture output
            old_stdout = sys.stdout
            sys.stdout = buffer = StringIO()
            
            try:
                from django.core.management import call_command
                call_command('showmigrations', '--plan', verbosity=0)
                migration_output = buffer.getvalue()
                
                if '[ ]' in migration_output:
                    db_health['checks'].append({
                        'test': 'migrations',
                        'status': 'warning',
                        'message': 'Unapplied migrations found'
                    })
                    db_health['status'] = 'degraded'
                else:
                    db_health['checks'].append({
                        'test': 'migrations',
                        'status': 'pass',
                        'message': 'All migrations applied'
                    })
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            db_health['checks'].append({
                'test': 'migrations',
                'status': 'error',
                'error': str(e)
            })
        
        return Response(db_health)
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': f'Database health check failed: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def celery_health(request):
    """
    Detailed Celery health check
    """
    try:
        celery_health = {
            'status': 'healthy',
            'timestamp': time.time(),
            'workers': [],
            'queues': [],
            'scheduled_tasks': []
        }
        
        inspect = celery_app.control.inspect()
        
        # Worker status
        try:
            stats = inspect.stats()
            active = inspect.active()
            registered = inspect.registered()
            
            if stats:
                for worker_name, worker_stats in stats.items():
                    worker_info = {
                        'name': worker_name,
                        'status': 'online',
                        'pool': worker_stats.get('pool', {}),
                        'active_tasks': len(active.get(worker_name, [])) if active else 0,
                        'registered_tasks': len(registered.get(worker_name, [])) if registered else 0
                    }
                    celery_health['workers'].append(worker_info)
            else:
                celery_health['status'] = 'unhealthy'
                celery_health['error'] = 'No workers found'
                
        except Exception as e:
            celery_health['status'] = 'unhealthy'
            celery_health['error'] = f'Worker inspection failed: {str(e)}'
        
        # Queue status
        try:
            from celery import current_app
            queue_names = ['celery', 'high_priority', 'low_priority']  # Add your queue names
            
            for queue_name in queue_names:
                try:
                    # This is a simplified queue check
                    celery_health['queues'].append({
                        'name': queue_name,
                        'status': 'available'
                    })
                except Exception as e:
                    celery_health['queues'].append({
                        'name': queue_name,
                        'status': 'error',
                        'error': str(e)
                    })
        except Exception as e:
            celery_health['queue_error'] = str(e)
        
        # Scheduled tasks (beat)
        try:
            scheduled = inspect.scheduled()
            if scheduled:
                for worker, tasks in scheduled.items():
                    celery_health['scheduled_tasks'].extend(tasks)
        except Exception as e:
            celery_health['beat_error'] = str(e)
        
        return Response(celery_health)
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': f'Celery health check failed: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def cache_health(request):
    """
    Detailed cache health check
    """
    try:
        cache_health = {
            'status': 'healthy',
            'timestamp': time.time(),
            'tests': []
        }
        
        # Test basic cache operations
        test_key = f'health_check_{int(time.time())}'
        test_value = 'health_check_value'
        
        # Write test
        start_time = time.time()
        cache.set(test_key, test_value, 60)
        write_time = (time.time() - start_time) * 1000
        
        cache_health['tests'].append({
            'operation': 'write',
            'status': 'pass',
            'response_time_ms': round(write_time, 2)
        })
        
        # Read test
        start_time = time.time()
        cached_value = cache.get(test_key)
        read_time = (time.time() - start_time) * 1000
        
        if cached_value == test_value:
            cache_health['tests'].append({
                'operation': 'read',
                'status': 'pass',
                'response_time_ms': round(read_time, 2)
            })
        else:
            cache_health['tests'].append({
                'operation': 'read',
                'status': 'fail',
                'error': 'Value mismatch'
            })
            cache_health['status'] = 'unhealthy'
        
        # Delete test
        start_time = time.time()
        cache.delete(test_key)
        delete_time = (time.time() - start_time) * 1000
        
        # Verify deletion
        if cache.get(test_key) is None:
            cache_health['tests'].append({
                'operation': 'delete',
                'status': 'pass',
                'response_time_ms': round(delete_time, 2)
            })
        else:
            cache_health['tests'].append({
                'operation': 'delete',
                'status': 'fail',
                'error': 'Value not deleted'
            })
            cache_health['status'] = 'degraded'
        
        # Cache backend info
        try:
            cache_health['backend'] = {
                'type': cache.__class__.__name__,
                'location': getattr(cache, '_cache', {}).get('_server', 'unknown')
            }
        except:
            pass
        
        return Response(cache_health)
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': f'Cache health check failed: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def email_health(request):
    """
    Email system health check
    """
    try:
        email_health = {
            'status': 'healthy',
            'timestamp': time.time(),
            'smtp_test': {},
            'configurations': []
        }
        
        # Test Django default email settings
        try:
            from django.core.mail import get_connection
            from django.conf import settings
            
            if settings.EMAIL_HOST and settings.EMAIL_HOST_USER:
                connection = get_connection()
                connection.open()
                connection.close()
                
                email_health['smtp_test'] = {
                    'status': 'pass',
                    'host': settings.EMAIL_HOST,
                    'port': settings.EMAIL_PORT,
                    'use_tls': settings.EMAIL_USE_TLS,
                    'use_ssl': settings.EMAIL_USE_SSL
                }
            else:
                email_health['smtp_test'] = {
                    'status': 'not_configured',
                    'message': 'Django email settings not configured'
                }
                
        except Exception as e:
            email_health['smtp_test'] = {
                'status': 'fail',
                'error': str(e)
            }
            email_health['status'] = 'degraded'
        
        # Check user email configurations
        try:
            active_configs = UserEmailConfiguration.objects.filter(is_active=True).count()
            total_configs = UserEmailConfiguration.objects.count()
            
            email_health['configurations'] = {
                'total': total_configs,
                'active': active_configs,
                'inactive': total_configs - active_configs
            }
            
            if active_configs == 0 and email_health['smtp_test'].get('status') != 'pass':
                email_health['status'] = 'unhealthy'
                email_health['error'] = 'No working email configuration found'
                
        except Exception as e:
            email_health['configurations'] = {
                'error': str(e)
            }
        
        return Response(email_health)
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': f'Email health check failed: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def application_health(request):
    """
    Application-specific health checks
    """
    try:
        app_health = {
            'status': 'healthy',
            'timestamp': time.time(),
            'components': {}
        }
        
        # Check critical models
        try:
            user_count = User.objects.count()
            app_health['components']['users'] = {
                'status': 'healthy',
                'count': user_count
            }
        except Exception as e:
            app_health['components']['users'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            app_health['status'] = 'unhealthy'
        
        # Check batches if available
        try:
            from batches.models import Batch
            batch_count = Batch.objects.count()
            active_batches = Batch.objects.filter(status='running').count()
            
            app_health['components']['batches'] = {
                'status': 'healthy',
                'total': batch_count,
                'active': active_batches
            }
        except ImportError:
            app_health['components']['batches'] = {
                'status': 'not_available',
                'message': 'Batches app not installed'
            }
        except Exception as e:
            app_health['components']['batches'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check email logs if available
        try:
            from logs.models import EmailLog
            from django.utils import timezone
            from datetime import timedelta
            
            recent_logs = EmailLog.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            failed_logs = EmailLog.objects.filter(
                status='failed',
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            app_health['components']['email_logs'] = {
                'status': 'healthy',
                'recent_24h': recent_logs,
                'failed_24h': failed_logs,
                'success_rate': round((recent_logs - failed_logs) / recent_logs * 100, 2) if recent_logs > 0 else 100
            }
            
            if failed_logs > recent_logs * 0.1:  # More than 10% failure rate
                app_health['components']['email_logs']['status'] = 'degraded'
                app_health['status'] = 'degraded'
                
        except ImportError:
            app_health['components']['email_logs'] = {
                'status': 'not_available',
                'message': 'Logs app not installed'
            }
        except Exception as e:
            app_health['components']['email_logs'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        return Response(app_health)
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': f'Application health check failed: {str(e)}'
        }, status=500)
"""
Enhanced Multi-Tenant Email Service
Handles different email providers and authentication methods
"""
import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from emails.provider_configs import get_provider_config, get_smtp_settings
from .models import UserEmailConfiguration

logger = logging.getLogger(__name__)


class MultiTenantEmailService:
    """Centralized email service for multi-tenant system"""
    
    @staticmethod
    def get_email_backend(email_config):
        """
        Get appropriate email backend based on configuration and environment
        """
        # Development mode - use console backend
        if settings.DEBUG and getattr(settings, 'EMAIL_BACKEND', '') == 'django.core.mail.backends.console.EmailBackend':
            logger.info(f"Development mode: Using console email backend for {email_config.provider}")
            return ConsoleBackend()
        
        # Production mode - use provider-specific backend
        return MultiTenantEmailService._get_provider_backend(email_config)
    
    @staticmethod
    def _get_provider_backend(email_config):
        """Get provider-specific email backend"""
        provider = email_config.provider
        provider_config = get_provider_config(provider)
        
        if not provider_config:
            raise ValueError(f"Unsupported email provider: {provider}")
        
        auth_type = provider_config.get('auth_type', 'password')
        
        if auth_type == 'oauth2':
            # OAuth providers (Gmail API, Outlook Graph API)
            return MultiTenantEmailService._get_oauth_backend(email_config)
        
        elif auth_type in ['password', 'app_password', 'bridge']:
            # SMTP providers
            return MultiTenantEmailService._get_smtp_backend(email_config)
        
        else:
            raise ValueError(f"Unsupported auth type: {auth_type}")
    
    @staticmethod
    def _get_smtp_backend(email_config):
        """Get SMTP backend for password-based providers"""
        smtp_settings = get_smtp_settings(email_config.provider)
        
        # Use config-specific settings or fallback to provider defaults
        host = email_config.email_host or smtp_settings.get('host')
        port = email_config.email_port or smtp_settings.get('port', 587)
        use_tls = email_config.email_use_tls if email_config.email_use_tls is not None else smtp_settings.get('tls', True)
        use_ssl = email_config.email_use_ssl if email_config.email_use_ssl is not None else smtp_settings.get('ssl', False)
        
        # Decrypt password
        password = email_config.decrypt_password()
        
        if not host or not email_config.email_host_user or not password:
            raise ValueError(f"Incomplete SMTP configuration for {email_config.provider}")
        
        logger.info(f"Creating SMTP backend for {email_config.provider}: {host}:{port}")
        
        return EmailBackend(
            host=host,
            port=port,
            username=email_config.email_host_user,
            password=password,
            use_tls=use_tls,
            use_ssl=use_ssl,
            fail_silently=False
        )
    
    @staticmethod
    def _get_oauth_backend(email_config):
        """Get OAuth backend for API-based providers (future implementation)"""
        # For now, fallback to SMTP if OAuth tokens are not available
        # TODO: Implement Gmail API and Microsoft Graph API support
        logger.warning(f"OAuth not yet implemented for {email_config.provider}, falling back to SMTP")
        return MultiTenantEmailService._get_smtp_backend(email_config)
    
    @staticmethod
    def send_email(email_config, subject, body, to_email, from_name=None, is_html=False):
        """
        Send email using tenant's configuration
        """
        try:
            # Development mode - print to console
            if settings.DEBUG and getattr(settings, 'EMAIL_BACKEND', '') == 'django.core.mail.backends.console.EmailBackend':
                return MultiTenantEmailService._send_console_email(
                    email_config, subject, body, to_email, from_name, is_html
                )
            
            # Production mode - use actual backend
            backend = MultiTenantEmailService.get_email_backend(email_config)
            
            # Prepare from header
            from_name = from_name or email_config.from_name or email_config.from_email
            from_header = f"{from_name} <{email_config.from_email}>" if from_name != email_config.from_email else email_config.from_email
            
            # Create email message
            email_message = EmailMessage(
                subject=subject,
                body=body,
                from_email=from_header,
                to=[to_email],
                connection=backend
            )
            
            if is_html:
                email_message.content_subtype = 'html'
            
            # Send email
            result = email_message.send()
            logger.info(f"Email sent successfully to {to_email} via {email_config.provider}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via {email_config.provider}: {str(e)}")
            raise
    
    @staticmethod
    def _send_console_email(email_config, subject, body, to_email, from_name, is_html):
        """Send email to console for development"""
        from_name = from_name or email_config.from_name or email_config.from_email
        from_header = f"{from_name} <{email_config.from_email}>" if from_name != email_config.from_email else email_config.from_email
        
        print(f"\n" + "="*80)
        print(f"📧 DEVELOPMENT EMAIL OUTPUT ({email_config.provider.upper()})")
        print(f"="*80)
        print(f"From: {from_header}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Provider: {email_config.provider}")
        print(f"Content Type: {'HTML' if is_html else 'Text'}")
        print(f"-"*80)
        print(body)
        print(f"="*80)
        
        return 1  # Simulate successful sending
    
    @staticmethod
    def test_configuration(email_config):
        """
        Test email configuration without sending actual email
        """
        try:
            # In development mode, always return success
            if settings.DEBUG:
                logger.info(f"Development mode: Email config test for {email_config.provider} - PASSED (simulated)")
                return True, "Configuration test passed (development mode)"
            
            # In production, try to create backend without sending
            backend = MultiTenantEmailService.get_email_backend(email_config)
            
            # Try to open connection
            if hasattr(backend, 'open'):
                backend.open()
                backend.close()
            
            logger.info(f"Email configuration test for {email_config.provider} - PASSED")
            return True, "Configuration test passed"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Email configuration test for {email_config.provider} - FAILED: {error_msg}")
            return False, f"Configuration test failed: {error_msg}"
    
    @staticmethod
    def get_configuration_instructions(provider):
        """Get setup instructions for a specific provider"""
        provider_config = get_provider_config(provider)
        return provider_config.get('setup_instructions', [])
    
    @staticmethod
    def validate_configuration(email_config):
        """Validate email configuration completeness"""
        provider_config = get_provider_config(email_config.provider)
        
        if not provider_config:
            return False, f"Unknown provider: {email_config.provider}"
        
        required_fields = provider_config.get('required_fields', [])
        auth_type = provider_config.get('auth_type', 'password')
        
        # Check basic fields
        if not email_config.from_email:
            return False, "From email is required"
        
        # Check provider-specific requirements
        if auth_type in ['password', 'app_password', 'bridge']:
            if not email_config.email_host_user:
                return False, "Email username is required"
            
            if not email_config.decrypt_password():
                return False, "Email password is required"
            
            # Check SMTP settings for custom provider
            if email_config.provider == 'smtp':
                if not email_config.email_host:
                    return False, "SMTP host is required for custom configuration"
        
        elif auth_type == 'oauth2':
            # TODO: Add OAuth validation when implemented
            pass
        
        return True, "Configuration is valid"


class EmailConfigurationHelper:
    """Helper class for email configuration management"""
    
    @staticmethod
    def auto_configure_smtp_settings(email_config):
        """Auto-configure SMTP settings based on provider"""
        smtp_settings = get_smtp_settings(email_config.provider)
        
        if smtp_settings and smtp_settings.get('host') != 'Custom':
            email_config.email_host = smtp_settings.get('host', '')
            email_config.email_port = smtp_settings.get('port', 587)
            email_config.email_use_tls = smtp_settings.get('tls', True)
            email_config.email_use_ssl = smtp_settings.get('ssl', False)
            
            logger.info(f"Auto-configured SMTP settings for {email_config.provider}")
    
    @staticmethod
    def get_provider_recommendations(provider):
        """Get recommendations for specific provider setup"""
        provider_config = get_provider_config(provider)
        
        recommendations = []
        auth_type = provider_config.get('auth_type')
        
        if auth_type == 'app_password':
            recommendations.append("💡 Use app-specific password instead of regular password")
            recommendations.append("🔐 Enable 2-Factor Authentication if required")
        
        elif auth_type == 'oauth2':
            recommendations.append("🚀 OAuth provides better security than SMTP")
            recommendations.append("📈 Higher API rate limits than SMTP")
        
        elif provider == 'smtp':
            recommendations.append("⚙️ Verify SMTP settings with your email provider")
            recommendations.append("🔍 Test configuration before saving")
        
        return recommendations

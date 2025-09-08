from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from core.permissions import IsTenantMember, IsTenantOwner
from core.models import UserEmailConfiguration
from core.serializers import UserEmailConfigurationSerializer
from core.email_service import MultiTenantEmailService
from logs.models import EmailLog
from .models import EmailTemplate
from .serializers import EmailTemplateSerializer, EmailTemplatePreviewSerializer
from .provider_configs import get_provider_config, get_all_providers
import re
import logging

logger = logging.getLogger(__name__)


class EmailTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        if self.request.user.role in ['super_admin', 'support_team']:
            return EmailTemplate.objects.all()
        elif self.request.user.tenant:
            return EmailTemplate.objects.filter(tenant=self.request.user.tenant)
        return EmailTemplate.objects.none()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsTenantMember(), IsTenantOwner()]
        return [IsAuthenticated(), IsTenantMember()]
    
    def perform_create(self, serializer):
        print(f"DEBUG: Creating template - Request data: {self.request.data}")
        print(f"DEBUG: User: {self.request.user}, Tenant: {self.request.user.tenant}")
        
        if self.request.user.role != 'super_admin':
            print(f"DEBUG: Setting tenant to: {self.request.user.tenant}")
            serializer.save(tenant=self.request.user.tenant)
        else:
            print("DEBUG: Super admin creating template")
            serializer.save()
    
    def _replace_template_variables(self, text, variables_dict, recipient_name=None, recipient_email=None):
        """Enhanced template variable replacement with better handling"""
        if not text:
            return text
        
        # Built-in variables
        if recipient_name:
            text = text.replace('{{recipient_name}}', recipient_name)
            text = text.replace('{{ recipient_name }}', recipient_name)  # Handle spaces
        if recipient_email:
            text = text.replace('{{recipient_email}}', recipient_email)
            text = text.replace('{{ recipient_email }}', recipient_email)  # Handle spaces
        
        # Custom variables from variables_dict
        for key, value in variables_dict.items():
            # Handle both {{key}} and {{ key }} formats
            text = text.replace(f'{{{{{key}}}}}', str(value))
            text = text.replace(f'{{{{ {key} }}}}', str(value))
        
        return text
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        try:
            template = self.get_object()
            print(f"[PREVIEW] Preview request for template: {template.name} by user: {request.user.username}")
            
            # Handle empty request data
            request_data = request.data if request.data else {}
            print(f"[PREVIEW] Preview data received: {request_data}")
            
            serializer = EmailTemplatePreviewSerializer(data=request_data)
            
            if serializer.is_valid():
                data = serializer.validated_data
                
                template_vars = data.get('template_variables', {})
                recipient_name = data.get('recipient_name', 'John Doe')
                recipient_email = data.get('recipient_email', 'john.doe@example.com')
                
                print(f"[PREVIEW] Processing template variables: {template_vars}")
                
                # Use enhanced replacement method
                subject = self._replace_template_variables(
                    template.subject, template_vars, recipient_name, recipient_email
                )
                body = self._replace_template_variables(
                    template.body, template_vars, recipient_name, recipient_email
                )
                
                # Extract all variables for frontend reference
                all_variables = self._extract_variables(template.subject + template.body)
                
                response_data = {
                    'subject': subject,
                    'body': body,
                    'is_html': template.is_html,
                    'template_variables_used': all_variables,
                    'template_info': {
                        'id': template.id,
                        'name': template.name,
                        'description': template.description or ''
                    },
                    'preview_context': {
                        'recipient_name': recipient_name,
                        'recipient_email': recipient_email,
                        'custom_variables': template_vars
                    }
                }
                
                print(f"[OK] Preview generated successfully")
                return Response(response_data)
            else:
                print(f"[ERROR] Serializer validation failed: {serializer.errors}")
                # Return preview anyway with default values
                subject = self._replace_template_variables(
                    template.subject, {}, 'John Doe', 'john.doe@example.com'
                )
                body = self._replace_template_variables(
                    template.body, {}, 'John Doe', 'john.doe@example.com'
                )
                
                return Response({
                    'subject': subject,
                    'body': body,
                    'is_html': template.is_html,
                    'template_variables_used': self._extract_variables(template.subject + template.body),
                    'warning': 'Preview generated with default values due to invalid input data'
                })
        
        except Exception as e:
            print(f"[ERROR] Error generating preview: {str(e)}")
            return Response(
                {'error': f'Failed to generate preview: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        try:
            template = self.get_object()
            print(f"[TEST] Test email request for template: {template.name} by user: {request.user.username}")
            
            test_email = request.data.get('test_email')
            template_vars = request.data.get('template_variables', {})
            
            print(f"[TEST] Test email details - To: {test_email}, Variables: {template_vars}")
            
            if not test_email:
                print("[ERROR] No test email provided")
                return Response({'error': 'test_email is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate email format
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(test_email)
            except ValidationError:
                print(f"[ERROR] Invalid email format: {test_email}")
                return Response({'error': 'Invalid email format'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Enhanced email configuration detection with better fallbacks
            sender_email = None
            sender_name = None
            
            # Try to get tenant email configuration first
            if hasattr(request.user, 'tenant') and request.user.tenant:
                tenant_email = request.user.tenant.emails.filter(is_active=True).first()
                
                if tenant_email:
                    sender_email = tenant_email.email
                    sender_name = tenant_email.display_name or tenant_email.email
                else:
                    # Find tenant admin (owner/admin role) email
                    from core.models import User
                    tenant_admin = User.objects.filter(
                        tenant=request.user.tenant,
                        role__in=['tenant_admin', 'staff_admin']
                    ).first()
                    
                    if tenant_admin and tenant_admin.email:
                        sender_email = tenant_admin.email
                        sender_name = f"{tenant_admin.first_name} {tenant_admin.last_name}".strip() or tenant_admin.username
            
            # Fallback to current user's email if no tenant config found
            if not sender_email:
                sender_email = request.user.email
                sender_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            
            # Final fallback to system configured email
            if not sender_email:
                from django.conf import settings
                sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@recalliq.com')
                sender_name = 'RecallIQ System'
            
            if not sender_email:
                return Response({
                    'error': 'No email configuration found. Please configure SMTP settings or set up tenant email configuration.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
            # Use enhanced replacement method
            subject = self._replace_template_variables(
                template.subject, template_vars, "Test User", test_email
            )
            body = self._replace_template_variables(
                template.body, template_vars, "Test User", test_email
            )
            
            subject = f"[TEST] {subject}"
            
            print(f"[TEST] Preparing to send test email:")
            print(f"[TEST]    From: {sender_name} <{sender_email}>")
            print(f"[TEST]    To: {test_email}")
            print(f"[TEST]    Subject: {subject}")
            print(f"[TEST]    HTML: {template.is_html}")
            
            # Create email log entry
            email_log = EmailLog.objects.create(
                tenant=request.user.tenant,
                email_type='test',
                direction='outgoing',
                from_email=sender_email,
                to_email=test_email,
                subject=subject,
                body=body,
                status='queued',
                sent_by_user=request.user
            )
            
            try:
                # Check if we have SMTP configuration
                from django.conf import settings
                if not getattr(settings, 'EMAIL_HOST_USER', None):
                    raise Exception("SMTP not configured. Please configure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in settings.")
                
                # Send the email
                print(f"[TEST] Sending email via SMTP...")
                send_mail(
                    subject=subject,
                    message=body if not template.is_html else '',
                    html_message=body if template.is_html else None,
                    from_email=f"{sender_name} <{sender_email}>" if sender_name else sender_email,
                    recipient_list=[test_email],
                    fail_silently=False
                )
                
                # Update log status
                email_log.status = 'sent'
                email_log.sent_at = timezone.now()
                email_log.save()
                
                print(f"[OK] Test email sent successfully!")
                
                return Response({
                    'message': 'Test email sent successfully',
                    'sender': sender_email,
                    'sender_name': sender_name,
                    'email_log_id': email_log.id,
                    'template_used': template.name
                })
                
            except Exception as e:
                print(f"[ERROR] Failed to send test email: {str(e)}")
                
                # Update log status
                email_log.status = 'failed'
                email_log.error_message = str(e)
                email_log.save()
                
                # Return detailed error information
                error_message = str(e)
                if 'authentication' in error_message.lower():
                    error_message = "SMTP authentication failed. Please check email credentials."
                elif 'connection' in error_message.lower():
                    error_message = "Could not connect to SMTP server. Please check email settings."
                
                return Response({
                    'error': f'Failed to send test email: {error_message}',
                    'email_log_id': email_log.id,
                    'sender_attempted': sender_email
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            print(f"[ERROR] Unexpected error in test email: {str(e)}")
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def variables(self, request, pk=None):
        template = self.get_object()
        variables = self._extract_variables(template.subject + template.body)
        
        return Response({
            'variables': variables,
            'predefined_variables': ['recipient_name', 'recipient_email']
        })
    
    def _extract_variables(self, text):
        """Enhanced variable extraction with better pattern matching"""
        if not text:
            return []
        
        # Pattern to match {{variable}} and {{ variable }} (with or without spaces)
        pattern = r'\{\{\s*([^}]+?)\s*\}\}'
        variables = re.findall(pattern, text)
        
        # Clean up variables and remove built-in ones for custom variable list
        cleaned_variables = []
        builtin_vars = ['recipient_name', 'recipient_email']
        
        for var in variables:
            var = var.strip()
            if var and var not in builtin_vars:
                cleaned_variables.append(var)
        
        return list(set(cleaned_variables))
    
    @action(detail=False, methods=['get'])
    def provider_configs(self, request):
        """Get email provider configuration information"""
        provider = request.query_params.get('provider')
        
        if provider:
            # Get specific provider configuration
            config = get_provider_config(provider)
            if not config:
                return Response(
                    {'error': f'Provider {provider} not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response({
                'provider': provider,
                'config': config
            })
        else:
            # Get all providers
            all_providers = get_all_providers()
            provider_list = []
            
            for provider_key in all_providers:
                config = get_provider_config(provider_key)
                provider_list.append({
                    'key': provider_key,
                    'name': config.get('name', provider_key.title()),
                    'auth_type': config.get('auth_type', 'password'),
                    'description': config.get('description', '')
                })
            
            return Response({
                'providers': provider_list
            })


class EmailConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing multi-tenant email configurations"""
    
    serializer_class = UserEmailConfigurationSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        """Filter configurations by tenant"""
        if hasattr(self.request.user, 'tenant'):
            return UserEmailConfiguration.objects.filter(tenant=self.request.user.tenant)
        return UserEmailConfiguration.objects.none()
    
    def perform_create(self, serializer):
        """Set tenant when creating configuration"""
        if hasattr(self.request.user, 'tenant'):
            serializer.save(tenant=self.request.user.tenant)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def test_configuration(self, request, pk=None):
        """Test email configuration"""
        try:
            config = self.get_object()
            
            # Validate configuration first
            is_valid, validation_message = MultiTenantEmailService.validate_configuration(config)
            
            if not is_valid:
                return Response({
                    'success': False,
                    'message': f'Configuration validation failed: {validation_message}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Test configuration
            if settings.DEBUG:
                # In development, simulate test
                return Response({
                    'success': True,
                    'message': f'Configuration test passed (development mode) for {config.provider}',
                    'provider': config.provider
                })
            else:
                # In production, run actual test
                success, message = MultiTenantEmailService.test_configuration(config)
                return Response({
                    'success': success,
                    'message': message,
                    'provider': config.provider
                })
            
        except Exception as e:
            logger.error(f"Error testing configuration {pk}: {str(e)}")
            return Response({
                'success': False,
                'message': f'Test failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def send_test_email(self, request, pk=None):
        """Send test email using configuration"""
        try:
            config = self.get_object()
            test_email = request.data.get('test_email')
            
            if not test_email:
                return Response({
                    'success': False,
                    'message': 'Test email address is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate configuration first
            is_valid, validation_message = MultiTenantEmailService.validate_configuration(config)
            
            if not is_valid:
                return Response({
                    'success': False,
                    'message': f'Configuration validation failed: {validation_message}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Send test email
            if settings.DEBUG:
                # In development, simulate sending
                logger.info(f"Development mode: Simulated test email to {test_email} using {config.provider}")
                return Response({
                    'success': True,
                    'message': f'Test email simulated for {test_email} using {config.provider} (development mode)',
                    'provider': config.provider
                })
            else:
                # In production, send actual email
                subject = f"Test Email from {config.provider}"
                body = f"""
                <h2>Email Configuration Test</h2>
                <p>This is a test email to verify your email configuration.</p>
                <p><strong>Provider:</strong> {config.provider}</p>
                <p><strong>From Email:</strong> {config.from_email}</p>
                <p><strong>Test Time:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>If you receive this email, your configuration is working correctly!</p>
                """
                
                result = MultiTenantEmailService.send_email(
                    email_config=config,
                    subject=subject,
                    body=body,
                    to_email=test_email,
                    is_html=True
                )
                
                if result:
                    return Response({
                        'success': True,
                        'message': f'Test email sent successfully to {test_email}',
                        'provider': config.provider
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'Test email sending failed',
                        'provider': config.provider
                    })
            
        except Exception as e:
            logger.error(f"Error sending test email for configuration {pk}: {str(e)}")
            return Response({
                'success': False,
                'message': f'Test email failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def active_configuration(self, request):
        """Get active email configuration for current tenant"""
        try:
            if not hasattr(request.user, 'tenant'):
                return Response({
                    'success': False,
                    'message': 'No tenant associated with user'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            config = UserEmailConfiguration.objects.filter(
                tenant=request.user.tenant,
                is_active=True
            ).first()
            
            if config:
                serializer = self.get_serializer(config)
                return Response({
                    'success': True,
                    'configuration': serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'No active email configuration found'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Error fetching active configuration: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error fetching configuration: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        """Set configuration as active (deactivates others for tenant)"""
        try:
            config = self.get_object()
            
            # Deactivate all other configurations for this tenant
            UserEmailConfiguration.objects.filter(
                tenant=config.tenant
            ).update(is_active=False)
            
            # Activate this configuration
            config.is_active = True
            config.save()
            
            logger.info(f"Set configuration {pk} as active for tenant {config.tenant.name}")
            
            return Response({
                'success': True,
                'message': f'Configuration set as active for {config.provider}'
            })
            
        except Exception as e:
            logger.error(f"Error setting configuration {pk} as active: {str(e)}")
            return Response({
                'success': False,
                'message': f'Failed to set as active: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
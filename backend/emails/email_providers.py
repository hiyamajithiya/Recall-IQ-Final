import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from django.conf import settings
from tenants.models import TenantMailSecret
import base64
import logging

logger = logging.getLogger(__name__)


class EmailProviderInterface:
    def send_email(self, from_email, to_email, subject, body, is_html=False):
        raise NotImplementedError("Subclasses must implement send_email method")


class SMTPProvider(EmailProviderInterface):
    def __init__(self, mail_secret):
        self.mail_secret = mail_secret
        self.credentials = mail_secret.decrypt_credentials()
    
    def send_email(self, from_email, to_email, subject, body, is_html=False):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(
                self.credentials.get('smtp_host', 'smtp.gmail.com'),
                self.credentials.get('smtp_port', 587)
            )
            server.starttls()
            server.login(
                self.credentials['username'],
                self.credentials['password']
            )
            
            server.send_message(msg)
            server.quit()
            
            return True, "Email sent successfully"
            
        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}")
            return False, str(e)


class GmailAPIProvider(EmailProviderInterface):
    def __init__(self, mail_secret):
        self.mail_secret = mail_secret
        self.credentials_data = mail_secret.decrypt_credentials()
        self.service = self._build_service()
    
    def _build_service(self):
        try:
            creds = Credentials.from_authorized_user_info(
                self.credentials_data,
                ['https://www.googleapis.com/auth/gmail.send']
            )
            
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self.mail_secret.encrypt_credentials(json.loads(creds.to_json()))
                self.mail_secret.save()
            
            return build('gmail', 'v1', credentials=creds)
            
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {str(e)}")
            raise
    
    def send_email(self, from_email, to_email, subject, body, is_html=False):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            
            message = {'raw': raw_message}
            
            result = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            return True, f"Message sent successfully. ID: {result['id']}"
            
        except Exception as e:
            logger.error(f"Gmail API send failed: {str(e)}")
            return False, str(e)


class OutlookProvider(EmailProviderInterface):
    def __init__(self, mail_secret):
        self.mail_secret = mail_secret
        self.credentials = mail_secret.decrypt_credentials()
    
    def send_email(self, from_email, to_email, subject, body, is_html=False):
        try:
            import requests
            
            access_token = self.credentials.get('access_token')
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            email_data = {
                'message': {
                    'subject': subject,
                    'body': {
                        'contentType': 'HTML' if is_html else 'Text',
                        'content': body
                    },
                    'toRecipients': [
                        {
                            'emailAddress': {
                                'address': to_email
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/sendMail',
                headers=headers,
                json=email_data
            )
            
            if response.status_code == 202:
                return True, "Email sent successfully via Outlook"
            else:
                return False, f"Outlook API error: {response.text}"
                
        except Exception as e:
            logger.error(f"Outlook send failed: {str(e)}")
            return False, str(e)


# Provider-specific SMTP configurations
PROVIDER_CONFIGS = {
    'gmail_smtp': {
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False
    },
    'outlook_smtp': {
        'smtp_host': 'smtp-mail.outlook.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False
    },
    'yahoo': {
        'smtp_host': 'smtp.mail.yahoo.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False
    },
    'rediffmail': {
        'smtp_host': 'smtp.rediffmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False
    },
    'hotmail': {
        'smtp_host': 'smtp-mail.outlook.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False
    },
    'aol': {
        'smtp_host': 'smtp.aol.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False
    },
    'zoho': {
        'smtp_host': 'smtp.zoho.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False
    },
    'icloud': {
        'smtp_host': 'smtp.mail.me.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False
    },
    'protonmail': {
        'smtp_host': 'mail.protonmail.ch',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False
    }
}


class ConfigurableSMTPProvider(EmailProviderInterface):
    """SMTP Provider with predefined configurations for popular email services"""
    
    def __init__(self, mail_secret):
        self.mail_secret = mail_secret
        self.credentials = mail_secret.decrypt_credentials()
        self.provider_type = mail_secret.provider
        
        # Get provider-specific configuration
        if self.provider_type in PROVIDER_CONFIGS:
            self.config = PROVIDER_CONFIGS[self.provider_type]
        else:
            # Fall back to generic SMTP with user-provided settings
            self.config = {
                'smtp_host': self.credentials.get('smtp_host', 'smtp.gmail.com'),
                'smtp_port': self.credentials.get('smtp_port', 587),
                'use_tls': self.credentials.get('use_tls', True),
                'use_ssl': self.credentials.get('use_ssl', False)
            }
    
    def send_email(self, from_email, to_email, subject, body, is_html=False):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Create SMTP connection
            if self.config.get('use_ssl', False):
                server = smtplib.SMTP_SSL(
                    self.config['smtp_host'],
                    self.config['smtp_port']
                )
            else:
                server = smtplib.SMTP(
                    self.config['smtp_host'],
                    self.config['smtp_port']
                )
                
                if self.config.get('use_tls', True):
                    server.starttls()
            
            # Login with credentials
            server.login(
                self.credentials['username'],
                self.credentials['password']
            )
            
            server.send_message(msg)
            server.quit()
            
            return True, f"Email sent successfully via {self.provider_type.upper()}"
            
        except Exception as e:
            logger.error(f"{self.provider_type.upper()} send failed: {str(e)}")
            return False, str(e)


class EmailProviderFactory:
    @staticmethod
    def get_provider(tenant_email):
        try:
            mail_secret = TenantMailSecret.objects.get(
                tenant_email=tenant_email,
                is_active=True
            )
            
            if mail_secret.provider == 'gmail':
                return GmailAPIProvider(mail_secret)
            elif mail_secret.provider == 'outlook':
                return OutlookProvider(mail_secret)
            elif mail_secret.provider in ['smtp', 'gmail_smtp', 'outlook_smtp', 'yahoo', 
                                        'rediffmail', 'hotmail', 'aol', 'zoho', 'icloud', 'protonmail']:
                return ConfigurableSMTPProvider(mail_secret)
            else:
                raise ValueError(f"Unsupported email provider: {mail_secret.provider}")
                
        except TenantMailSecret.DoesNotExist:
            raise ValueError("No mail secret configured for this tenant email")
    
    @staticmethod
    def send_email_via_provider(tenant_email, to_email, subject, body, is_html=False):
        provider = EmailProviderFactory.get_provider(tenant_email)
        return provider.send_email(
            from_email=tenant_email.email,
            to_email=to_email,
            subject=subject,
            body=body,
            is_html=is_html
        )
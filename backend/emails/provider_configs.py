"""
Email provider configuration instructions and settings
"""

EMAIL_PROVIDER_CONFIGS = {
    'gmail': {
        'name': 'Gmail API',
        'auth_type': 'oauth2',
        'description': 'Uses Gmail API with OAuth 2.0 authentication for secure email sending.',
        'setup_instructions': [
            "1. Go to Google Cloud Console",
            "2. Create a new project or select existing one",
            "3. Enable Gmail API",
            "4. Create credentials (OAuth 2.0 Client IDs)",
            "5. Download credentials JSON file",
            "6. Configure OAuth consent screen"
        ],
        'smtp_settings': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'tls': True,
            'ssl': False
        },
        'rate_limits': {
            'daily': 1000000000,
            'per_second': 250
        },
        'features': ['html', 'attachments', 'tracking'],
        'required_fields': ['client_id', 'client_secret', 'refresh_token']
    },
    
    'gmail_smtp': {
        'name': 'Gmail SMTP',
        'auth_type': 'app_password',
        'description': 'Uses Gmail SMTP server with app-specific password.',
        'setup_instructions': [
            "1. Enable 2-Factor Authentication on your Gmail account",
            "2. Go to Google Account Settings > Security",
            "3. Generate an App Password for 'Mail'",
            "4. Use your Gmail address as username",
            "5. Use the 16-character app password (not your regular password)"
        ],
        'smtp_settings': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'tls': True,
            'ssl': False
        },
        'rate_limits': {
            'daily': 500,
            'per_hour': 100
        },
        'features': ['html', 'attachments'],
        'required_fields': ['email', 'app_password']
    },
    
    'outlook': {
        'name': 'Outlook/Hotmail SMTP',
        'auth_type': 'password',
        'description': 'Uses Outlook SMTP server with regular password.',
        'setup_instructions': [
            "1. Make sure SMTP access is enabled in your Outlook settings",
            "2. Use your full Outlook/Hotmail email address as username",
            "3. Use your regular account password",
            "4. If you have 2FA enabled, you might need an app password"
        ],
        'smtp_settings': {
            'host': 'smtp-mail.outlook.com',
            'port': 587,
            'tls': True,
            'ssl': False
        },
        'rate_limits': {
            'daily': 300,
            'per_minute': 30
        },
        'features': ['html', 'attachments'],
        'required_fields': ['email', 'password']
    },
    
    'yahoo': {
        'name': 'Yahoo Mail SMTP',
        'auth_type': 'app_password',
        'description': 'Uses Yahoo SMTP server with app-specific password.',
        'setup_instructions': [
            "1. Enable 2-Factor Authentication on your Yahoo account",
            "2. Go to Yahoo Account Security settings",
            "3. Generate an App Password for 'Mail'",
            "4. Use your Yahoo email address as username",
            "5. Use the generated app password"
        ],
        'smtp_settings': {
            'host': 'smtp.mail.yahoo.com',
            'port': 587,
            'tls': True,
            'ssl': False
        },
        'rate_limits': {
            'daily': 500,
            'per_hour': 100
        },
        'features': ['html', 'attachments'],
        'required_fields': ['email', 'app_password']
    },
    
    'smtp': {
        'name': 'Custom SMTP',
        'auth_type': 'password',
        'description': 'Custom SMTP server configuration.',
        'setup_instructions': [
            "1. Get SMTP server details from your email provider",
            "2. Ensure you have correct host, port, and security settings",
            "3. Verify authentication credentials",
            "4. Test connection before saving"
        ],
        'smtp_settings': {
            'host': 'Custom',
            'port': 587,
            'tls': True,
            'ssl': False
        },
        'rate_limits': {
            'daily': 'Provider dependent',
            'per_hour': 'Provider dependent'
        },
        'features': ['html', 'attachments'],
        'required_fields': ['host', 'port', 'email', 'password']
    }
}


def get_provider_config(provider):
    """Get configuration for a specific email provider"""
    return EMAIL_PROVIDER_CONFIGS.get(provider)


def get_smtp_settings(provider):
    """Get SMTP settings for a provider"""
    config = EMAIL_PROVIDER_CONFIGS.get(provider, {})
    return config.get('smtp_settings', {})


def get_all_providers():
    """Get list of all supported providers"""
    return list(EMAIL_PROVIDER_CONFIGS.keys())


def get_providers_by_auth_type(auth_type):
    """Get providers that use specific authentication type"""
    providers = []
    for provider, config in EMAIL_PROVIDER_CONFIGS.items():
        if config.get('auth_type') == auth_type:
            providers.append(provider)
    return providers


def is_provider_supported(provider):
    """Check if provider is supported"""
    return provider in EMAIL_PROVIDER_CONFIGS

"""
Django settings module auto-selector
Automatically imports the appropriate settings based on environment
"""

import os

# Get environment from environment variable or default to development
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .staging import *
else:
    # Default to development
    from .development import *
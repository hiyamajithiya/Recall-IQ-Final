"""
Django settings for recalliq project.

This file imports the appropriate settings based on environment.
For development, use DJANGO_SETTINGS_MODULE=recalliq.settings.development
For production, use DJANGO_SETTINGS_MODULE=recalliq.settings.production
"""

import os
from decouple import config

# Determine which settings to import based on environment
environment = config('DJANGO_ENVIRONMENT', default='production')

if environment == 'production':
    from .settings.production import *
elif environment == 'test':
    from .settings.test import *
else:
    from .settings.development import *


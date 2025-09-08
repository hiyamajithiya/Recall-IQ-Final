"""
RecallIQ - Development Settings
For local development with enhanced debugging and testing tools
"""
from .base import *

# Development mode
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '94.136.184.80', 'recalliq.chinmaytechnosoft.com']

# Development database (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'recalliq_db'),
        'USER': os.getenv('DB_USER', 'recalliq_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'Chinmay@123'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 60,
        }
    }
}

# Development email backend
# Note: This project uses per-tenant email configurations stored in UserEmailConfiguration model
# Global Django settings are only used as fallback for system emails like password resets
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# For development, we'll use SMTP if configured, otherwise console
# This allows OTP emails to be sent while keeping other emails in console
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    print(f"[DEV] SMTP email backend enabled for OTP and system emails: {EMAIL_HOST}:{EMAIL_PORT}")
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("[DEV] Console email backend enabled - emails will be printed to console")

# Show email backend status
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
        print(f"[DEV] SMTP email backend configured for OTP and system emails")
    else:
        print(f"[DEV] Gmail SMTP available but using console backend for development")
    print(f"[DEV] Gmail SMTP: {EMAIL_HOST}:{EMAIL_PORT} ({EMAIL_HOST_USER})")
else:
    print("[DEV] Console email backend enabled - configure EMAIL_HOST_USER/PASSWORD for real emails")
    print("[DEV] OTP emails will be printed to console")

# Temporary: Back to working mode until Redis is installed
CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously - works without Redis
CELERY_TASK_EAGER_PROPAGATES = True  # Propagate exceptions
CELERY_BROKER_URL = 'memory://'  # Memory broker (no Redis needed)
CELERY_RESULT_BACKEND = 'django-db'  # Database result backend

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Development tools
if 'django_extensions' in INSTALLED_APPS:
    INSTALLED_APPS += ['django_extensions']

# Debug toolbar for development
if DEBUG and 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Enhanced logging for development
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
    'propagate': False,
}

# Development cache (dummy cache)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

print(f"[DEV] Development settings loaded")
print(f"[DEV] Database: SQLite ({DATABASES['default']['NAME']})")
print(f"[DEV] Email Backend: {EMAIL_BACKEND}")
print(f"[DEV] Celery Broker: {CELERY_BROKER_URL}")
print(f"[DEV] Debug Mode: {DEBUG}")

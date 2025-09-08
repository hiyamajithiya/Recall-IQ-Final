"""
RecallIQ - Production Settings
Enterprise-grade security and performance configuration
"""
from .base import *
import dj_database_url

# Production mode - Security critical
DEBUG = False

# Production hosts - Must be configured
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default='localhost,127.0.0.1',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Security Headers - Enterprise Grade
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# Session security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF protection
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True

# Production Database - PostgreSQL Required
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='postgresql://chinmay_admin:Chinmay@2018@94.136.184.80:5432/recalliq'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Alternative PostgreSQL configuration if DATABASE_URL not provided
if not config('DATABASE_URL', default=''):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='recalliq'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432', cast=int),
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'sslmode': config('DB_SSLMODE', default='require'),
            },
        }
    }

# Redis Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'recalliq',
        'TIMEOUT': 300,
    }
}

# Session store in Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Production Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# Celery optimizations for production
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'
CELERY_TASK_ROUTES = {
    'batches.tasks.send_batch_emails': {'queue': 'batch_processing'},
    'batches.tasks.send_individual_email_with_retry': {'queue': 'email_sending'},
    'batches.tasks.execute_batch_subcycle': {'queue': 'batch_processing'},
}
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Production Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# Email configuration validation
if not all([EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD]):
    raise ValueError(
        "Production email configuration incomplete. "
        "EMAIL_HOST, EMAIL_HOST_USER, and EMAIL_HOST_PASSWORD are required."
    )

# CORS settings for production
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

# File serving and static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Production logging
LOGGING['handlers']['file']['filename'] = '/var/log/recalliq/django.log'
LOGGING['handlers']['error_file'] = {
    'level': 'ERROR',
    'class': 'logging.FileHandler',
    'filename': '/var/log/recalliq/error.log',
    'formatter': 'verbose',
}
LOGGING['root']['handlers'].append('error_file')

# Error reporting - Sentry integration (optional)
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(auto_enabling_integrations=False),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# Security - Additional headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Password strength requirements for production
AUTH_PASSWORD_VALIDATORS += [
    {
        'NAME': 'core.validators.CustomPasswordValidator',
        'OPTIONS': {
            'min_length': 12,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digits': True,
            'require_symbols': True,
        }
    },
]

# Rate limiting (if django-ratelimit is installed)
RATELIMIT_ENABLE = True

# Admin security
ADMIN_URL = config('ADMIN_URL', default='admin/')

print(f"[PROD] Production settings loaded")
print(f"[PROD] Debug mode: {DEBUG}")
print(f"[PROD] Database: PostgreSQL")
print(f"[PROD] Cache: Redis")
print(f"[PROD] Email: SMTP ({EMAIL_HOST})")
print(f"[PROD] Security headers: Enabled")
print(f"[PROD] HTTPS redirect: {SECURE_SSL_REDIRECT}")
print(f"[PROD] HSTS: {SECURE_HSTS_SECONDS} seconds")

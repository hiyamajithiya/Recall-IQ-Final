"""
RecallIQ - Production-Ready Celery Configuration 🚀
Handles 1000+ tenants with Redis backend and advanced scheduling
"""
import os
import django
from celery import Celery
from django.conf import settings

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recalliq.settings')

# Initialize Django
django.setup()

# Create Celery app
app = Celery('recalliq')

# Load settings from Django configuration
app.config_from_object('django.conf:settings', namespace='CELERY')

# Production-Ready Configuration 🔥
app.conf.update(
    # Use Redis for production performance
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
    
    # Task routing for load balancing
    task_routes={
        'batches.tasks.send_batch_emails': {'queue': 'batch_emails'},
        'batches.tasks.schedule_recurring_batches': {'queue': 'scheduler'},
    },
    
    # Advanced settings for high performance
    worker_prefetch_multiplier=1,  # Memory efficient
    task_acks_late=True,  # Acknowledge after completion
    
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',  # IST timezone
    
    # Result expiration
    result_expires=3600,  # 1 hour
)

# Celery Beat Schedule - SUPERPOWER AUTOMATION! 🚀
app.conf.beat_schedule = {
    'check-scheduled-batches-every-minute': {
        'task': 'batches.tasks.schedule_recurring_batches',
        'schedule': 60.0,  # Every 60 seconds
        'options': {'queue': 'scheduler'}
    },
}

# Auto-discover tasks
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery functionality"""
    print(f'🚀 Celery Debug: {self.request!r}')
    return 'Celery is working in SUPERPOWER mode! 🔥'
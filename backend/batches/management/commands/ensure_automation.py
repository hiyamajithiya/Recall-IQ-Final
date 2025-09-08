"""
Django management command to ensure batch automation is always enabled.
This runs automatically on system startup to guarantee automation is active.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ensure batch automation is enabled and running'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of automation task',
        )

    def handle(self, *args, **options):
        """Automatically enable batch automation - no user intervention needed"""
        try:
            self.stdout.write('🚀 Ensuring batch automation is enabled...')
            
            # Create or enable the periodic task for automation
            crontab, created = CrontabSchedule.objects.get_or_create(
                minute='0',  # Every hour at minute 0
                hour='*',
                day_of_week='*',
                day_of_month='*',
                month_of_year='*'
            )
            
            if created:
                self.stdout.write(f'✅ Created crontab schedule: {crontab}')
            
            # Ensure the periodic task exists and is enabled
            periodic_task, task_created = PeriodicTask.objects.get_or_create(
                name='recurring-batch-processing',
                defaults={
                    'task': 'batches.tasks.schedule_recurring_batches',
                    'crontab': crontab,
                    'enabled': True
                }
            )
            
            if task_created:
                self.stdout.write('✅ Created new automation task')
            elif not periodic_task.enabled or options['force']:
                periodic_task.enabled = True
                periodic_task.save()
                self.stdout.write('✅ Enabled automation task')
            else:
                self.stdout.write('✅ Automation task already enabled')
            
            # Log the automation startup
            activity_logs = cache.get('batch_automation_logs', [])
            activity_logs.append(f"{timezone.now().strftime('%H:%M:%S')} - System startup: Automation auto-enabled")
            cache.set('batch_automation_logs', activity_logs[-50:], 86400)
            
            self.stdout.write(
                self.style.SUCCESS(
                    '🎯 Batch automation is now COMPULSORILY ENABLED and will run automatically!'
                )
            )
            self.stdout.write('📋 Automation will check for scheduled batches every hour')
            self.stdout.write('🔄 No user intervention required - automation runs silently')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to enable automation: {str(e)}')
            )
            logger.error(f"Automation startup error: {str(e)}")
            raise

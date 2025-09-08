"""
Django Management Command to Process Scheduled Batches
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from batches.models import Batch
from batches.tasks import send_batch_emails
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process all scheduled batches that are ready to execute'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-id',
            type=int,
            help='Process specific batch ID',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        batch_id = options.get('batch_id')
        
        if batch_id:
            # Process specific batch
            try:
                batch = Batch.objects.get(id=batch_id)
                self.stdout.write(f'Processing batch {batch.id}: {batch.name}')
                send_batch_emails(batch.id)
                self.stdout.write(self.style.SUCCESS(f'Successfully processed batch {batch.id}'))
            except Batch.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Batch {batch_id} not found'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing batch {batch_id}: {str(e)}'))
        else:
            # Process all scheduled batches
            scheduled_batches = Batch.objects.filter(
                status='scheduled',
                start_time__lte=now
            )
            
            batch_count = scheduled_batches.count()
            if batch_count > 0:
                self.stdout.write(f'Found {batch_count} batches to execute')
                
                for batch in scheduled_batches:
                    try:
                        self.stdout.write(f'Processing batch {batch.id}: {batch.name}')
                        send_batch_emails(batch.id)
                        self.stdout.write(self.style.SUCCESS(f'Successfully processed batch {batch.id}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error processing batch {batch.id}: {str(e)}'))
            else:
                self.stdout.write('No scheduled batches found to execute')

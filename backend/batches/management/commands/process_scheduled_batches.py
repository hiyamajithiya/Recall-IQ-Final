"""
Django management command to process scheduled email batches.
This command can be run independently or scheduled with cron/task scheduler.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from batches.models import Batch
from batches.tasks import send_batch_emails, execute_batch_subcycle
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process scheduled email batches automatically'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually executing',
        )
        parser.add_argument(
            '--batch-id',
            type=int,
            help='Process a specific batch ID',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(f"🚀 Checking for scheduled batches at {now}")
        
        # Handle specific batch or all scheduled batches
        if options['batch_id']:
            try:
                batch = Batch.objects.get(id=options['batch_id'])
                if batch.status != 'scheduled':
                    self.stdout.write(
                        self.style.WARNING(f"Batch {batch.id} is not scheduled (status: {batch.status})")
                    )
                    return
                batches_to_run = [batch]
            except Batch.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Batch {options['batch_id']} not found")
                )
                return
        else:
            # Get all scheduled batches that are due
            batches_to_run = Batch.objects.filter(
                status='scheduled',
                start_time__lte=now
            )
        
        self.stdout.write(f"📋 Found {len(batches_to_run)} batches to execute")
        
        if not batches_to_run:
            self.stdout.write(self.style.SUCCESS("✅ No batches due for execution"))
            return
        
        processed_count = 0
        failed_count = 0
        
        for batch in batches_to_run:
            try:
                # Check if batch has expired
                if batch.end_time and now > batch.end_time:
                    if not options['dry_run']:
                        batch.status = 'completed'
                        batch.save()
                    self.stdout.write(
                        self.style.WARNING(f"⏰ Batch {batch.id} expired - marked as completed")
                    )
                    continue
                
                self.stdout.write(f"🔄 Processing batch {batch.id}: {batch.name}")
                
                if options['dry_run']:
                    self.stdout.write(f"   📧 Would process {batch.batch_recipients.count()} recipients")
                    continue
                
                # Execute the batch synchronously
                if batch.sub_cycle_enabled:
                    self.stdout.write(f"   🔁 Executing sub-cycle batch {batch.id}")
                    execute_batch_subcycle(batch.id)
                else:
                    self.stdout.write(f"   📤 Executing batch {batch.id}")
                    send_batch_emails(batch.id)
                
                # Handle recurring batches
                if batch.interval_minutes > 0:
                    next_run_time = now + timezone.timedelta(minutes=batch.interval_minutes)
                    
                    if batch.end_time is None or next_run_time <= batch.end_time:
                        batch.start_time = next_run_time
                        batch.status = 'scheduled'
                        batch.save()
                        self.stdout.write(f"   🔄 Recurring batch scheduled for {next_run_time}")
                    else:
                        batch.status = 'completed'
                        batch.save()
                        self.stdout.write(f"   ✅ Recurring batch completed - end time reached")
                else:
                    self.stdout.write(f"   ✅ One-time batch {batch.id} started")
                
                processed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Successfully executed batch {batch.id}")
                )
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Error processing batch {batch.id}: {str(e)}")
                )
                if not options['dry_run']:
                    try:
                        batch.status = 'failed'
                        batch.save()
                    except:
                        pass
                continue
        
        # Summary
        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f"🔍 Dry run completed: {len(batches_to_run)} batches would be processed")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"🎉 Batch processing completed: {processed_count} successful, {failed_count} failed"
                )
            )

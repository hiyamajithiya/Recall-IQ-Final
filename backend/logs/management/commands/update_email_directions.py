from django.core.management.base import BaseCommand
from logs.models import EmailLog
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Update existing email logs to set correct direction based on sender and email type'

    def handle(self, *args, **options):
        self.stdout.write('Starting to update email log directions...')
        
        # Get all email logs that need updating
        email_logs = EmailLog.objects.all()
        updated_count = 0
        
        for log in email_logs:
            original_direction = log.direction
            
            # Determine correct direction based on logic:
            # If email is welcome/notification and sent by super_admin to tenant users, it's incoming
            # All other emails are outgoing (sent by the tenant)
            
            if log.email_type in ['welcome', 'notification']:
                # Check if sent by super admin
                if log.sent_by_user and log.sent_by_user.role == 'super_admin':
                    # This is a super admin sending to tenant, so it's incoming for the tenant
                    log.direction = 'incoming'
                else:
                    # Sent by tenant user or system, so it's outgoing
                    log.direction = 'outgoing'
            else:
                # Batch, test, manual emails are typically outgoing (sent by tenant)
                log.direction = 'outgoing'
            
            # Only save if direction changed
            if log.direction != original_direction:
                log.save(update_fields=['direction'])
                updated_count += 1
                self.stdout.write(
                    f'Updated log {log.id}: {log.email_type} from {original_direction} to {log.direction}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} email log directions!')
        )

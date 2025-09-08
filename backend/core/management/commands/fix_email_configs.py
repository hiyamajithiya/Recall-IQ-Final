from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import UserEmailConfiguration

User = get_user_model()


class Command(BaseCommand):
    help = 'Diagnose and fix email configuration password encryption issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to check email configurations for'
        )
        parser.add_argument(
            '--config-id',
            type=int,
            help='Specific email configuration ID to check'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix issues by re-encrypting passwords'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='New password to set for the configuration (use with --fix)'
        )

    def handle(self, *args, **options):
        user = options.get('user')
        config_id = options.get('config_id')
        fix_mode = options.get('fix')
        new_password = options.get('password')

        self.stdout.write(self.style.SUCCESS('Email Configuration Diagnostics'))
        self.stdout.write('=' * 50)

        # Get configurations to check
        if config_id:
            try:
                configs = [UserEmailConfiguration.objects.get(id=config_id)]
            except UserEmailConfiguration.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Email configuration with ID {config_id} not found'))
                return
        elif user:
            try:
                user_obj = User.objects.get(username=user)
                configs = UserEmailConfiguration.objects.filter(user=user_obj)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {user} not found'))
                return
        else:
            configs = UserEmailConfiguration.objects.all()

        if not configs:
            self.stdout.write(self.style.WARNING('No email configurations found'))
            return

        for config in configs:
            self.stdout.write(f'\nChecking config: {config.name} (ID: {config.id})')
            self.stdout.write(f'User: {config.user.username}')
            self.stdout.write(f'From Email: {config.from_email}')
            self.stdout.write(f'Host: {config.email_host}:{config.email_port}')
            self.stdout.write(f'Active: {config.is_active}')
            self.stdout.write(f'Default: {config.is_default}')

            # Check encrypted password field
            has_encrypted = bool(config.encrypted_email_host_password)
            self.stdout.write(f'Has encrypted password: {has_encrypted}')
            
            if has_encrypted:
                encrypted_length = len(config.encrypted_email_host_password)
                self.stdout.write(f'Encrypted password length: {encrypted_length}')

                # Test decryption
                try:
                    decrypted = config.decrypt_password()
                    if decrypted:
                        self.stdout.write(self.style.SUCCESS(f'✓ Password decryption: SUCCESS (length: {len(decrypted)})'))
                    else:
                        self.stdout.write(self.style.ERROR('✗ Password decryption: FAILED (empty result)'))
                        
                        if fix_mode and new_password:
                            self.stdout.write('Attempting to fix with new password...')
                            config.encrypt_password(new_password)
                            config.save()
                            
                            # Test again
                            test_decrypt = config.decrypt_password()
                            if test_decrypt == new_password:
                                self.stdout.write(self.style.SUCCESS('✓ Password encryption fixed!'))
                            else:
                                self.stdout.write(self.style.ERROR('✗ Fix attempt failed'))
                                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'✗ Password decryption: ERROR - {e}'))
                    
                    if fix_mode and new_password:
                        self.stdout.write('Attempting to fix with new password...')
                        try:
                            config.encrypt_password(new_password)
                            config.save()
                            
                            # Test again
                            test_decrypt = config.decrypt_password()
                            if test_decrypt == new_password:
                                self.stdout.write(self.style.SUCCESS('✓ Password encryption fixed!'))
                            else:
                                self.stdout.write(self.style.ERROR('✗ Fix attempt failed'))
                        except Exception as fix_error:
                            self.stdout.write(self.style.ERROR(f'✗ Fix attempt failed: {fix_error}'))
            else:
                self.stdout.write(self.style.ERROR('✗ No encrypted password stored'))
                
                if fix_mode and new_password:
                    self.stdout.write('Setting new password...')
                    try:
                        config.encrypt_password(new_password)
                        config.save()
                        self.stdout.write(self.style.SUCCESS('✓ Password set successfully!'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'✗ Failed to set password: {e}'))

        if not fix_mode:
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(self.style.WARNING('To fix issues, run with --fix and --password options'))
            self.stdout.write('Example: python manage.py fix_email_configs --config-id 1 --fix --password "your_app_password"')
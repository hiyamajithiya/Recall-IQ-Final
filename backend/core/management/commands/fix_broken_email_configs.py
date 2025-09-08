"""
Management command to identify and help fix broken email configurations
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from cryptography.fernet import Fernet
from core.models import UserEmailConfiguration
import base64


class Command(BaseCommand):
    help = 'Identify and help fix broken email configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list-broken',
            action='store_true',
            help='List all broken email configurations',
        )
        parser.add_argument(
            '--test-key',
            action='store_true',
            help='Test current encryption key validity',
        )
        parser.add_argument(
            '--migrate-base64',
            action='store_true',
            help='Migrate base64 encoded passwords to Fernet encryption',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('[DIAGNOSTIC] Email Configuration Diagnostic Tool'))
        self.stdout.write('=' * 60)

        if options['test_key']:
            self.test_encryption_key()
        
        if options['list_broken']:
            self.list_broken_configs()
            
        if options['migrate_base64']:
            self.migrate_base64_passwords()
        
        if not any([options['test_key'], options['list_broken'], options['migrate_base64']]):
            self.show_help()

    def test_encryption_key(self):
        """Test if the current encryption key is valid"""
        self.stdout.write('\n[TEST] Testing encryption key...')
        
        if not hasattr(settings, 'ENCRYPTION_KEY') or not settings.ENCRYPTION_KEY:
            self.stdout.write(self.style.ERROR('[ERROR] No ENCRYPTION_KEY found in settings'))
            return False
        
        try:
            f = Fernet(settings.ENCRYPTION_KEY.encode())
            # Test encrypt/decrypt cycle
            test_data = "test_password_123"
            encrypted = f.encrypt(test_data.encode())
            decrypted = f.decrypt(encrypted).decode()
            
            if decrypted == test_data:
                self.stdout.write(self.style.SUCCESS('[OK] Encryption key is valid and working'))
                return True
            else:
                self.stdout.write(self.style.ERROR('[ERROR] Encryption key failed validation'))
                return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] Encryption key test failed: {e}'))
            return False

    def list_broken_configs(self):
        """List all email configurations that cannot be decrypted"""
        self.stdout.write('\n[CHECK] Checking all email configurations...')
        
        configs = UserEmailConfiguration.objects.all()
        broken_configs = []
        working_configs = []
        
        for config in configs:
            try:
                decrypted = config.decrypt_password()
                if decrypted:
                    working_configs.append(config)
                    self.stdout.write(f'[OK] {config.user.username} - {config.name}: Working')
                else:
                    broken_configs.append(config)
                    self.stdout.write(f'[FAIL] {config.user.username} - {config.name}: Cannot decrypt password')
            except Exception as e:
                broken_configs.append(config)
                self.stdout.write(f'[ERROR] {config.user.username} - {config.name}: Error - {e}')
        
        self.stdout.write(f'\n[SUMMARY] Results:')
        self.stdout.write(f'   Working configurations: {len(working_configs)}')
        self.stdout.write(f'   Broken configurations: {len(broken_configs)}')
        
        if broken_configs:
            self.stdout.write(f'\n[ATTENTION] Broken configurations need attention:')
            for config in broken_configs:
                self.stdout.write(f'   - User: {config.user.username}')
                self.stdout.write(f'     Config: {config.name}')
                self.stdout.write(f'     Email: {config.from_email}')
                self.stdout.write(f'     Encrypted data length: {len(config.encrypted_email_host_password)}')
                
                # Try to determine the encryption method
                try:
                    # Test if it's base64
                    base64.b64decode(config.encrypted_email_host_password.encode())
                    self.stdout.write(f'     Type: Likely base64 encoded')
                except:
                    if len(config.encrypted_email_host_password) > 20:
                        self.stdout.write(f'     Type: Likely Fernet encrypted (wrong key)')
                    else:
                        self.stdout.write(f'     Type: Unknown format')
                self.stdout.write('')
        
        return broken_configs

    def migrate_base64_passwords(self):
        """Migrate base64 encoded passwords to Fernet encryption"""
        self.stdout.write('\n[MIGRATE] Migrating base64 passwords to Fernet encryption...')
        
        if not self.test_encryption_key():
            self.stdout.write(self.style.ERROR('Cannot migrate - encryption key is not valid'))
            return
        
        configs = UserEmailConfiguration.objects.all()
        migrated = 0
        
        for config in configs:
            try:
                # Try Fernet decryption first
                if hasattr(settings, 'ENCRYPTION_KEY') and settings.ENCRYPTION_KEY:
                    try:
                        f = Fernet(settings.ENCRYPTION_KEY.encode())
                        f.decrypt(config.encrypted_email_host_password.encode())
                        # If this succeeds, it's already Fernet encrypted
                        continue
                    except:
                        # Fernet failed, try base64
                        pass
                
                # Try base64 decryption
                try:
                    decrypted = base64.b64decode(config.encrypted_email_host_password.encode()).decode()
                    # If we get here, it was base64 encoded
                    self.stdout.write(f'[MIGRATE] Migrating {config.user.username} - {config.name}')
                    
                    # Re-encrypt with Fernet
                    config.encrypt_password(decrypted)
                    config.save()
                    migrated += 1
                    
                    # Verify the migration worked
                    test_decrypt = config.decrypt_password()
                    if test_decrypt == decrypted:
                        self.stdout.write(f'[OK] Migration successful')
                    else:
                        self.stdout.write(f'[FAIL] Migration verification failed')
                        
                except Exception as e2:
                    self.stdout.write(f'[WARN] Cannot migrate {config.user.username} - {config.name}: {e2}')
                    
            except Exception as e:
                self.stdout.write(f'[ERROR] Error processing {config.user.username} - {config.name}: {e}')
        
        self.stdout.write(f'\n[COMPLETE] Migration complete. Migrated {migrated} configurations.')

    def show_help(self):
        """Show available options"""
        self.stdout.write('\n[HELP] Available options:')
        self.stdout.write('   --test-key      : Test if encryption key is valid')
        self.stdout.write('   --list-broken   : List configurations with decryption issues')
        self.stdout.write('   --migrate-base64: Migrate base64 passwords to Fernet encryption')
        self.stdout.write('\nExamples:')
        self.stdout.write('   python manage.py fix_broken_email_configs --test-key')
        self.stdout.write('   python manage.py fix_broken_email_configs --list-broken')
        self.stdout.write('   python manage.py fix_broken_email_configs --migrate-base64')
"""
Management command to test the notification system

This command helps verify that notifications are working properly
for tenant and user updates.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from core.tenant_notifications import (
    notify_generic_update, 
    notify_plan_change, 
    notify_status_change
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the notification system for tenant and user updates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Tenant ID to test notifications for',
        )
        parser.add_argument(
            '--test-type',
            type=str,
            choices=['tenant', 'user', 'all'],
            default='all',
            help='Type of notification to test',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting notification system test...'))
        
        # Get or create test data
        tenant = self.get_test_tenant(options.get('tenant_id'))
        admin_user = self.get_admin_user()
        
        if not tenant:
            self.stdout.write(self.style.ERROR('No tenant found for testing'))
            return
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found for testing'))
            return
        
        test_type = options.get('test_type', 'all')
        
        if test_type in ['tenant', 'all']:
            self.test_tenant_notifications(tenant, admin_user)
        
        if test_type in ['user', 'all']:
            self.test_user_notifications(tenant, admin_user)
        
        self.stdout.write(self.style.SUCCESS('Notification test completed!'))

    def get_test_tenant(self, tenant_id=None):
        """Get a tenant for testing"""
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Tenant with ID {tenant_id} not found'))
                return None
        
        # Get the first available tenant
        tenant = Tenant.objects.first()
        if tenant:
            self.stdout.write(f'Using tenant: {tenant.name} (ID: {tenant.id})')
        return tenant

    def get_admin_user(self):
        """Get an admin user for testing"""
        admin = User.objects.filter(role='super_admin').first()
        if not admin:
            admin = User.objects.filter(role='tenant_admin').first()
        
        if admin:
            self.stdout.write(f'Using admin user: {admin.username} ({admin.role})')
        return admin

    def test_tenant_notifications(self, tenant, admin_user):
        """Test tenant update notifications"""
        self.stdout.write(self.style.WARNING('\n=== Testing Tenant Notifications ==='))
        
        # Test plan change notification
        try:
            result = notify_plan_change(tenant, 'starter', 'professional', admin_user)
            status = "✅ SUCCESS" if result else "❌ FAILED"
            self.stdout.write(f'{status} Plan change notification')
        except Exception as e:
            self.stdout.write(f'❌ FAILED Plan change notification: {e}')
        
        # Test status change notification
        try:
            result = notify_status_change(tenant, 'active', 'trial', admin_user)
            status = "✅ SUCCESS" if result else "❌ FAILED"
            self.stdout.write(f'{status} Status change notification')
        except Exception as e:
            self.stdout.write(f'❌ FAILED Status change notification: {e}')
        
        # Test generic update notification
        try:
            changes = {
                'contact_email': {'old': 'old@example.com', 'new': tenant.contact_email},
                'billing_email': {'old': 'billing@example.com', 'new': tenant.billing_email}
            }
            result = notify_generic_update(tenant, changes, admin_user)
            status = "✅ SUCCESS" if result else "❌ FAILED"
            self.stdout.write(f'{status} Generic update notification')
        except Exception as e:
            self.stdout.write(f'❌ FAILED Generic update notification: {e}')

    def test_user_notifications(self, tenant, admin_user):
        """Test user update notifications"""
        self.stdout.write(self.style.WARNING('\n=== Testing User Update Notifications ==='))
        
        # Find a test user in the tenant
        test_user = User.objects.filter(tenant=tenant).exclude(id=admin_user.id).first()
        
        if not test_user:
            self.stdout.write('⚠️  No test user found in tenant, creating one...')
            test_user = User.objects.create_user(
                username=f'test_user_{tenant.id}',
                email=f'test_{tenant.id}@example.com',
                password='testpass123',
                role='staff',
                tenant=tenant,
                created_by=admin_user
            )
            self.stdout.write(f'Created test user: {test_user.username}')
        
        # Test user update notification
        try:
            changes = {
                'user_update': {'old': 'Previous Staff Details', 'new': 'Updated Staff Details'},
                'updated_user_id': test_user.id,
                'updated_user_name': f"{test_user.first_name} {test_user.last_name}".strip() or test_user.username,
                'updated_user_email': test_user.email,
                'updated_user_role': test_user.get_role_display(),
                'changes': {
                    'email': {'old': 'old@example.com', 'new': test_user.email},
                    'role': {'old': 'User', 'new': 'Staff'}
                }
            }
            result = notify_generic_update(tenant, changes, admin_user)
            status = "✅ SUCCESS" if result else "❌ FAILED"
            self.stdout.write(f'{status} User update notification')
        except Exception as e:
            self.stdout.write(f'❌ FAILED User update notification: {e}')
        
        self.stdout.write(f'Used test user: {test_user.username} (ID: {test_user.id})')
"""
RecallIQ - Management command to create superuser with tenant
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tenants.models import Tenant

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with an associated tenant for RecallIQ'
    
    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username for the RecallIQ superuser')
        parser.add_argument('--email', required=True, help='Email for the RecallIQ superuser')
        parser.add_argument('--password', required=True, help='Password for the RecallIQ superuser')
        parser.add_argument('--tenant-name', required=False, help='Name of the RecallIQ tenant organization')
    
    def handle(self, *args, **options):
        tenant, created = Tenant.objects.get_or_create(
            name=options['tenant_name'],
            defaults={
                'contact_email': options['email'],
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f"Created tenant: {tenant.name}")
        else:
            self.stdout.write(f"Using existing tenant: {tenant.name}")
        
        user, created = User.objects.get_or_create(
            username=options['username'],
            defaults={
                'email': options['email'],
                'role': 'super_admin',
                'tenant': tenant,
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            user.set_password(options['password'])
            user.save()
            self.stdout.write(f"Created superuser: {user.username}")
        else:
            self.stdout.write(f"User {user.username} already exists")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up RecallIQ superuser "{user.username}" with tenant "{tenant.name}"'
            )
        )
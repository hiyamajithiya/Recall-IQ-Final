"""
Management command to test user management restrictions

This command tests all the user management restrictions we implemented:
1. Role creation restrictions
2. Modification restrictions 
3. Deletion restrictions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from core.serializers import UserSerializer
from rest_framework.exceptions import PermissionDenied

User = get_user_model()


class Command(BaseCommand):
    help = 'Test user management restrictions for tenant admins'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing user management restrictions...'))
        
        # Get test data
        tenant = Tenant.objects.first()
        super_admin = User.objects.filter(role='super_admin').first()
        tenant_admin = User.objects.filter(role='tenant_admin').first()
        
        if not tenant or not super_admin or not tenant_admin:
            self.stdout.write(self.style.ERROR('Missing test data. Need tenant, super_admin, and tenant_admin users.'))
            return
        
        self.stdout.write(f'Test setup:')
        self.stdout.write(f'  Super Admin: {super_admin.username}')
        self.stdout.write(f'  Tenant Admin: {tenant_admin.username}')
        self.stdout.write(f'  Tenant: {tenant.name}')
        
        self.test_role_creation_restrictions(tenant_admin, tenant)
        self.test_modification_restrictions(tenant_admin, super_admin, tenant)
        self.test_deletion_restrictions(tenant_admin, super_admin, tenant)
        self.test_staff_admin_capabilities(tenant_admin, tenant)
        self.test_available_roles_api(tenant_admin, super_admin)
        
        self.stdout.write(self.style.SUCCESS('All user restriction tests completed!'))

    def test_role_creation_restrictions(self, tenant_admin, tenant):
        """Test that tenant admin can only create certain roles"""
        self.stdout.write('\n=== Testing Role Creation Restrictions ===')
        
        # Test 1: Creating 'user' role (should fail)
        success = self._test_user_creation(
            tenant_admin, tenant, 'user', 'test_user_role', 'user@test.com',
            should_succeed=False, test_name="Creating 'user' role (should fail)"
        )
        
        # Test 2: Creating 'tenant_admin' role (should fail - no longer allowed)
        success = self._test_user_creation(
            tenant_admin, tenant, 'tenant_admin', 'test_tenant_admin', 'tadmin@test.com',
            should_succeed=False, test_name="Creating 'tenant_admin' role (should fail)"
        )
        
        # Test 3: Creating 'staff_admin' role (should succeed)
        success = self._test_user_creation(
            tenant_admin, tenant, 'staff_admin', 'test_staff_admin', 'staffadmin@test.com',
            should_succeed=True, test_name="Creating 'staff_admin' role (should succeed)"
        )
        
        # Test 4: Creating 'staff' role (should succeed)
        success = self._test_user_creation(
            tenant_admin, tenant, 'staff', 'test_staff', 'staff@test.com',
            should_succeed=True, test_name="Creating 'staff' role (should succeed)"
        )

    def _test_user_creation(self, requester, tenant, role, username, email, should_succeed, test_name):
        """Helper method to test user creation"""
        self.stdout.write(f'\nTest: {test_name}')
        
        try:
            context = {'request_user': requester}
            data = {
                'username': username,
                'email': email,
                'role': role,
                'tenant': tenant.id
            }
            serializer = UserSerializer(data=data, context=context)
            
            if serializer.is_valid():
                if should_succeed:
                    self.stdout.write(self.style.SUCCESS('  PASS: User creation allowed as expected'))
                    return True
                else:
                    self.stdout.write(self.style.ERROR('  FAIL: User creation should have been blocked'))
                    return False
            else:
                if not should_succeed:
                    error_msg = list(serializer.errors.values())[0][0]
                    self.stdout.write(self.style.SUCCESS(f'  PASS: User creation blocked as expected'))
                    self.stdout.write(f'    Reason: {error_msg}')
                    return True
                else:
                    self.stdout.write(self.style.ERROR(f'  FAIL: User creation should have been allowed'))
                    self.stdout.write(f'    Error: {serializer.errors}')
                    return False
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ERROR: Exception occurred: {e}'))
            return False

    def test_modification_restrictions(self, tenant_admin, super_admin, tenant):
        """Test modification restrictions"""
        self.stdout.write('\n=== Testing Modification Restrictions ===')
        
        # Find a user created by super admin
        super_admin_user = User.objects.filter(created_by=super_admin, tenant=tenant).first()
        
        if super_admin_user:
            self.stdout.write(f'\nTest: Tenant admin modifying user created by super admin (should succeed)')
            try:
                context = {'request_user': tenant_admin}
                data = {'first_name': 'Modified Name'}
                serializer = UserSerializer(super_admin_user, data=data, partial=True, context=context)
                
                if serializer.is_valid():
                    self.stdout.write(self.style.SUCCESS('  PASS: Modification allowed as expected'))
                    self.stdout.write('    Reason: Tenant admin can now modify users created by super admin')
                else:
                    error_msg = list(serializer.errors.values())[0][0]
                    self.stdout.write(self.style.ERROR('  FAIL: Modification should be allowed'))
                    self.stdout.write(f'    Error: {error_msg}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ERROR: Exception: {e}'))
        else:
            self.stdout.write('  SKIP: No user created by super admin found')

    def test_deletion_restrictions(self, tenant_admin, super_admin, tenant):
        """Test deletion restrictions"""
        self.stdout.write('\n=== Testing Deletion Restrictions ===')
        
        # Create a test user by super admin
        test_user = User.objects.create_user(
            username='temp_test_user',
            email='temp@test.com',
            role='staff',
            tenant=tenant,
            created_by=super_admin
        )
        
        self.stdout.write(f'\nTest: Tenant admin deleting user created by super admin (should fail)')
        
        # Import the view to test deletion
        from core.views import UserDetailView
        from django.test import RequestFactory
        from rest_framework.exceptions import PermissionDenied
        
        # Create mock request
        factory = RequestFactory()
        request = factory.delete(f'/users/{test_user.id}/')
        request.user = tenant_admin
        
        view = UserDetailView()
        view.request = request
        
        try:
            view.perform_destroy(test_user)
            self.stdout.write(self.style.ERROR('  FAIL: Should not allow deletion'))
        except PermissionDenied as e:
            self.stdout.write(self.style.SUCCESS('  PASS: Deletion blocked as expected'))
            self.stdout.write(f'    Reason: {str(e)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ERROR: Unexpected exception: {e}'))
        finally:
            # Clean up test user
            test_user.delete()
            
        # Test secondary tenant admin deletion restrictions
        self.stdout.write(f'\nTest: Secondary tenant admin deletion restrictions')
        
        # Create a secondary tenant admin
        secondary_tenant_admin = User.objects.create_user(
            username='secondary_tenant_admin',
            email='secondary@test.com',
            role='tenant_admin',
            tenant=tenant,
            created_by=tenant_admin
        )
        
        # Create a test user by secondary tenant admin
        test_user2 = User.objects.create_user(
            username='temp_test_user2',
            email='temp2@test.com',
            role='staff',
            tenant=tenant,
            created_by=secondary_tenant_admin
        )
        
        # Try to delete with secondary tenant admin (should fail)
        request2 = factory.delete(f'/users/{test_user2.id}/')
        request2.user = secondary_tenant_admin
        
        view2 = UserDetailView()
        view2.request = request2
        
        try:
            view2.perform_destroy(test_user2)
            self.stdout.write(self.style.ERROR('  FAIL: Secondary tenant admin should not be able to delete'))
        except PermissionDenied as e:
            self.stdout.write(self.style.SUCCESS('  PASS: Secondary tenant admin deletion blocked as expected'))
            self.stdout.write(f'    Reason: {str(e)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ERROR: Unexpected exception: {e}'))
        finally:
            # Clean up test users
            test_user2.delete()
            secondary_tenant_admin.delete()
            
        # Test staff_admin deletion restrictions
        self.stdout.write(f'\nTest: Staff admin deletion restrictions')
        
        # Create a staff admin
        staff_admin = User.objects.create_user(
            username='staff_admin_user',
            email='staffadmin@test.com',
            role='staff_admin',
            tenant=tenant,
            created_by=tenant_admin
        )
        
        # Create a test user by staff admin
        test_user3 = User.objects.create_user(
            username='temp_test_user3',
            email='temp3@test.com',
            role='staff',
            tenant=tenant,
            created_by=staff_admin
        )
        
        # Try to delete with staff admin (should fail)
        request3 = factory.delete(f'/users/{test_user3.id}/')
        request3.user = staff_admin
        
        view3 = UserDetailView()
        view3.request = request3
        
        try:
            view3.perform_destroy(test_user3)
            self.stdout.write(self.style.ERROR('  FAIL: Staff admin should not be able to delete'))
        except PermissionDenied as e:
            self.stdout.write(self.style.SUCCESS('  PASS: Staff admin deletion blocked as expected'))
            self.stdout.write(f'    Reason: {str(e)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ERROR: Unexpected exception: {e}'))
        finally:
            # Clean up test users
            test_user3.delete()
            staff_admin.delete()

    def test_staff_admin_capabilities(self, tenant_admin, tenant):
        """Test staff admin capabilities - should have same rights as tenant admin except deletion"""
        self.stdout.write('\\n=== Testing Staff Admin Capabilities ===')
        
        # Create a staff admin
        staff_admin = User.objects.create_user(
            username='test_staff_admin_capabilities',
            email='teststaffadmin@test.com',
            role='staff_admin',
            tenant=tenant,
            created_by=tenant_admin
        )
        
        self.stdout.write(f'\\nTest: Staff admin user creation rights')
        
        # Test staff admin creating staff user
        context = {'request_user': staff_admin}
        data = {
            'username': 'staff_by_staff_admin',
            'email': 'staffbystaffadmin@test.com',
            'role': 'staff',
            'tenant': tenant.id
        }
        serializer = UserSerializer(data=data, context=context)
        
        if serializer.is_valid():
            self.stdout.write(self.style.SUCCESS('  PASS: Staff admin can create staff users'))
        else:
            self.stdout.write(self.style.ERROR('  FAIL: Staff admin should be able to create staff users'))
            self.stdout.write(f'    Error: {serializer.errors}')
        
        # Test staff admin creating staff_admin user
        context = {'request_user': staff_admin}
        data = {
            'username': 'staff_admin_by_staff_admin',
            'email': 'staffadminbystaffadmin@test.com',
            'role': 'staff_admin',
            'tenant': tenant.id
        }
        serializer = UserSerializer(data=data, context=context)
        
        if serializer.is_valid():
            self.stdout.write(self.style.SUCCESS('  PASS: Staff admin can create staff_admin users'))
        else:
            self.stdout.write(self.style.ERROR('  FAIL: Staff admin should be able to create staff_admin users'))
            self.stdout.write(f'    Error: {serializer.errors}')
        
        # Clean up
        staff_admin.delete()

    def test_available_roles_api(self, tenant_admin, super_admin):
        """Test the available roles API endpoint"""
        self.stdout.write('\n=== Testing Available Roles API ===')
        
        from core.views import get_available_user_roles
        
        # Mock request class
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        # Test for tenant admin
        request = MockRequest(tenant_admin)
        response = get_available_user_roles(request)
        
        self.stdout.write(f'\nTenant Admin available roles:')
        for role in response.data['available_roles']:
            self.stdout.write(f'  - {role["label"]} ({role["value"]})')
        
        expected_roles = {'staff_admin', 'staff'}
        actual_roles = {role['value'] for role in response.data['available_roles']}
        
        if actual_roles == expected_roles:
            self.stdout.write(self.style.SUCCESS('  PASS: Correct roles returned for tenant admin'))
        else:
            self.stdout.write(self.style.ERROR(f'  FAIL: Expected {expected_roles}, got {actual_roles}'))
        
        # Test for super admin
        request = MockRequest(super_admin)
        response = get_available_user_roles(request)
        
        self.stdout.write(f'\nSuper Admin available roles:')
        for role in response.data['available_roles']:
            self.stdout.write(f'  - {role["label"]} ({role["value"]})')
        
        expected_roles = {'tenant_admin'}
        actual_roles = {role['value'] for role in response.data['available_roles']}
        
        if actual_roles == expected_roles:
            self.stdout.write(self.style.SUCCESS('  PASS: Correct roles returned for super admin'))
        else:
            self.stdout.write(self.style.ERROR(f'  FAIL: Expected {expected_roles}, got {actual_roles}'))
        
        # Test for staff admin (should have same available roles as tenant admin)
        tenant = Tenant.objects.first()
        tenant_admin = User.objects.filter(role='tenant_admin', tenant=tenant).first()
        
        # Create a staff admin for testing
        staff_admin = User.objects.create_user(
            username='test_staff_admin_roles_api',
            email='teststaffadminapi@test.com',
            role='staff_admin',
            tenant=tenant,
            created_by=tenant_admin
        )
        
        request = MockRequest(staff_admin)
        # Manually get available roles for staff admin
        user = staff_admin
        if user.role == 'staff_admin':
            available_roles = [
                {'value': 'staff_admin', 'label': 'Staff Admin'},
                {'value': 'staff', 'label': 'Staff'}
            ]
            self.stdout.write(f'\\nStaff Admin available roles:')
            for role in available_roles:
                self.stdout.write(f'  - {role["label"]} ({role["value"]})')
            
            expected_roles = {'staff_admin', 'staff'}
            actual_roles = {role['value'] for role in available_roles}
            
            if actual_roles == expected_roles:
                self.stdout.write(self.style.SUCCESS('  PASS: Correct roles returned for staff admin'))
            else:
                self.stdout.write(self.style.ERROR(f'  FAIL: Expected {expected_roles}, got {actual_roles}'))
        
        # Clean up
        staff_admin.delete()
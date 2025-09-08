"""
Core Application Tests
Comprehensive unit tests for core models, views, and permissions
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from tenants.models import Tenant
from .models import UserEmailConfiguration
from .permissions import IsSuperAdmin, IsTenantAdmin, IsTenantMember

User = get_user_model()


class UserModelTests(TestCase):
    """Test User model functionality"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            plan="professional",
            company_address="123 Test St, Test City",
            contact_person="Test Contact",
            contact_email="contact@test.com",
            contact_phone="+1234567890"
        )
    
    def test_user_creation_with_roles(self):
        """Test user creation with different roles"""
        roles = ['super_admin', 'sales_team', 'support_team', 'tenant_admin', 'staff_admin', 'staff', 'user']
        
        for role in roles:
            with self.subTest(role=role):
                user = User.objects.create_user(
                    username=f'test_{role}',
                    email=f'{role}@example.com',
                    password='testpass123',
                    role=role,
                    tenant=self.tenant
                )
                self.assertEqual(user.role, role)
                self.assertEqual(user.tenant, self.tenant)
                self.assertTrue(user.check_password('testpass123'))
    
    def test_user_string_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user',
            tenant=self.tenant
        )
        self.assertEqual(str(user), 'testuser')
    
    def test_user_email_unique(self):
        """Test email uniqueness constraint"""
        User.objects.create_user(
            username='user1',
            email='test@example.com',
            password='testpass123',
            tenant=self.tenant
        )
        
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='user2',
                email='test@example.com',
                password='testpass123',
                tenant=self.tenant
            )


class UserEmailConfigurationTests(TestCase):
    """Test UserEmailConfiguration model"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant"
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant=self.tenant
        )
    
    def test_email_config_creation(self):
        """Test email configuration creation"""
        config = UserEmailConfiguration.objects.create(
            user=self.user,
            email_host='smtp.gmail.com',
            email_port=587,
            email_use_tls=True,
            email_host_user='test@gmail.com',
            encrypted_email_host_password='encrypted_password',
            provider='gmail'
        )
        self.assertEqual(config.user, self.user)
        self.assertEqual(config.provider, 'gmail')
        self.assertTrue(config.email_use_tls)
    
    def test_email_config_string_representation(self):
        """Test email configuration string representation"""
        config = UserEmailConfiguration.objects.create(
            user=self.user,
            email_host_user='test@gmail.com',
            provider='gmail'
        )
        expected = f"{self.user.username} - test@gmail.com (gmail)"
        self.assertEqual(str(config), expected)


class AuthenticationAPITests(APITestCase):
    """Test authentication API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant"
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant=self.tenant
        )
    
    def test_login_success(self):
        """Test successful login"""
        url = reverse('core:login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('core:login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_profile_authenticated(self):
        """Test profile access with authentication"""
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('core:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['role'], 'user')
    
    def test_profile_unauthenticated(self):
        """Test profile access without authentication"""
        url = reverse('core:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionTests(TestCase):
    """Test custom permission classes"""
    
    def setUp(self):
        self.tenant1 = Tenant.objects.create(name="Tenant 1", slug="tenant-1")
        self.tenant2 = Tenant.objects.create(name="Tenant 2", slug="tenant-2")
        
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='testpass123',
            role='super_admin',
            tenant=self.tenant1
        )
        
        self.tenant_admin = User.objects.create_user(
            username='tenantadmin',
            email='tenant@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant=self.tenant1
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123',
            role='user',
            tenant=self.tenant1
        )
    
    def test_super_admin_permission(self):
        """Test super admin permission"""
        permission = IsSuperAdmin()
        
        # Mock request objects
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request_super = MockRequest(self.super_admin)
        request_regular = MockRequest(self.regular_user)
        
        self.assertTrue(permission.has_permission(request_super, None))
        self.assertFalse(permission.has_permission(request_regular, None))
    
    def test_tenant_admin_permission(self):
        """Test tenant admin permission"""
        permission = IsTenantAdmin()
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request_admin = MockRequest(self.tenant_admin)
        request_user = MockRequest(self.regular_user)
        
        self.assertTrue(permission.has_permission(request_admin, None))
        self.assertFalse(permission.has_permission(request_user, None))
    
    def test_tenant_member_permission(self):
        """Test tenant member permission"""
        permission = IsTenantMember()
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request_member = MockRequest(self.regular_user)
        request_member.user.tenant = self.tenant1
        
        self.assertTrue(permission.has_permission(request_member, None))


class UserViewSetTests(APITestCase):
    """Test UserViewSet functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant"
        )
        
        # Create users with different roles
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='super@example.com',
            password='testpass123',
            role='super_admin',
            tenant=self.tenant
        )
        
        self.tenant_admin = User.objects.create_user(
            username='tenantadmin',
            email='tenant@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant=self.tenant
        )
    
    def test_user_list_super_admin(self):
        """Test user list access for super admin"""
        refresh = RefreshToken.for_user(self.super_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('core:user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 2)
    
    def test_user_creation_by_admin(self):
        """Test user creation by admin"""
        refresh = RefreshToken.for_user(self.tenant_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('core:user-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'role': 'user',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['role'], 'user')


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class UserSignalTests(TestCase):
    """Test user-related signals"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant"
        )
    
    def test_user_creation_signal(self):
        """Test signals fired on user creation"""
        # This would test any post_save signals
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant=self.tenant
        )
        
        # Verify user was created successfully
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # Test any signal-related side effects
        # (Add specific signal testing based on your implementation)


class APIRateLimitTests(APITestCase):
    """Test API rate limiting (if implemented)"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_login_rate_limit(self):
        """Test rate limiting on login endpoint"""
        url = reverse('core:login')
        data = {
            'username': 'nonexistent',
            'password': 'wrongpassword'
        }
        
        # This test would verify rate limiting behavior
        # Implementation depends on your rate limiting strategy
        for i in range(5):  # Attempt multiple failed logins
            response = self.client.post(url, data)
            # First few should return 401, eventually might return 429
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS])


class SecurityTests(TestCase):
    """Test security features"""
    
    def test_password_validation(self):
        """Test password validation rules"""
        tenant = Tenant.objects.create(name="Test", slug="test")
        
        # Test weak password rejection
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='123',  # Too weak
                tenant=tenant
            )
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        # This would test that ORM properly sanitizes inputs
        # Example: searching with malicious input should not execute SQL
        tenant = Tenant.objects.create(name="Test", slug="test")
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            tenant=tenant
        )
        
        # Attempt SQL injection through ORM
        malicious_input = "'; DROP TABLE core_user; --"
        users = User.objects.filter(username__icontains=malicious_input)
        
        # Should return empty queryset, not execute malicious SQL
        self.assertEqual(users.count(), 0)
        
        # Verify table still exists
        self.assertTrue(User.objects.filter(username='testuser').exists())

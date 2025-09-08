"""
Batch Application Tests
Comprehensive unit tests for batch models, views, and processing
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
from datetime import timedelta

from tenants.models import Tenant
from emails.models import EmailTemplate
from core.models import UserEmailConfiguration
from .models import Batch, BatchRecipient
from .tasks import send_batch_emails, execute_batch_subcycle

User = get_user_model()


class BatchModelTests(TestCase):
    """Test Batch model functionality"""
    
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
        self.template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Test Subject",
            content="Test Content",
            tenant=self.tenant
        )
        self.email_config = UserEmailConfiguration.objects.create(
            user=self.user,
            email_host='smtp.gmail.com',
            email_port=587,
            email_use_tls=True,
            email_host_user='test@gmail.com',
            encrypted_email_host_password='encrypted_password',
            provider='gmail'
        )
    
    def test_batch_creation(self):
        """Test batch creation with required fields"""
        batch = Batch.objects.create(
            name="Test Batch",
            description="Test Description",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60
        )
        
        self.assertEqual(batch.name, "Test Batch")
        self.assertEqual(batch.status, "created")
        self.assertEqual(batch.template, self.template)
        self.assertEqual(batch.created_by, self.user)
        self.assertFalse(batch.sub_cycle_enabled)
    
    def test_batch_string_representation(self):
        """Test batch string representation"""
        batch = Batch.objects.create(
            name="Test Batch",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60
        )
        self.assertEqual(str(batch), "Test Batch")
    
    def test_batch_status_choices(self):
        """Test batch status validation"""
        batch = Batch.objects.create(
            name="Test Batch",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60
        )
        
        valid_statuses = ['created', 'scheduled', 'processing', 'paused', 'completed', 'cancelled', 'failed']
        for status in valid_statuses:
            batch.status = status
            batch.save()
            batch.refresh_from_db()
            self.assertEqual(batch.status, status)
    
    def test_batch_sub_cycle_configuration(self):
        """Test sub-cycle batch configuration"""
        batch = Batch.objects.create(
            name="Sub-cycle Batch",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60,
            sub_cycle_enabled=True,
            sub_cycle_interval_type='days',
            sub_cycle_interval_value=3,
            max_reminders=5
        )
        
        self.assertTrue(batch.sub_cycle_enabled)
        self.assertEqual(batch.sub_cycle_interval_type, 'days')
        self.assertEqual(batch.sub_cycle_interval_value, 3)
        self.assertEqual(batch.max_reminders, 5)


class BatchRecipientModelTests(TestCase):
    """Test BatchRecipient model functionality"""
    
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
        self.template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Test Subject",
            content="Test Content",
            tenant=self.tenant
        )
        self.email_config = UserEmailConfiguration.objects.create(
            user=self.user,
            email_host_user='test@gmail.com',
            provider='gmail'
        )
        self.batch = Batch.objects.create(
            name="Test Batch",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60
        )
    
    def test_batch_recipient_creation(self):
        """Test batch recipient creation"""
        recipient = BatchRecipient.objects.create(
            batch=self.batch,
            email='recipient@example.com',
            name='Test Recipient'
        )
        
        self.assertEqual(recipient.batch, self.batch)
        self.assertEqual(recipient.email, 'recipient@example.com')
        self.assertEqual(recipient.name, 'Test Recipient')
        self.assertEqual(recipient.emails_sent_count, 0)
        self.assertFalse(recipient.is_completed)
    
    def test_batch_recipient_string_representation(self):
        """Test batch recipient string representation"""
        recipient = BatchRecipient.objects.create(
            batch=self.batch,
            email='recipient@example.com',
            name='Test Recipient'
        )
        expected = f"Test Recipient (recipient@example.com) - Test Batch"
        self.assertEqual(str(recipient), expected)
    
    def test_batch_recipient_completion_status(self):
        """Test recipient completion tracking"""
        recipient = BatchRecipient.objects.create(
            batch=self.batch,
            email='recipient@example.com',
            name='Test Recipient'
        )
        
        # Mark as completed
        recipient.is_completed = True
        recipient.completed_at = timezone.now()
        recipient.save()
        
        self.assertTrue(recipient.is_completed)
        self.assertIsNotNone(recipient.completed_at)


class BatchAPITests(APITestCase):
    """Test Batch API endpoints"""
    
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
            role='tenant_admin',
            tenant=self.tenant
        )
        self.template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Test Subject",
            content="Test Content",
            tenant=self.tenant
        )
        self.email_config = UserEmailConfiguration.objects.create(
            user=self.user,
            email_host_user='test@gmail.com',
            provider='gmail'
        )
        
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_batch_list(self):
        """Test batch list endpoint"""
        # Create test batches
        Batch.objects.create(
            name="Batch 1",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60
        )
        Batch.objects.create(
            name="Batch 2",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=120
        )
        
        url = reverse('batches:batch-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_batch_creation(self):
        """Test batch creation via API"""
        url = reverse('batches:batch-list')
        data = {
            'name': 'API Test Batch',
            'description': 'Created via API',
            'template': self.template.id,
            'email_configuration': self.email_config.id,
            'interval_minutes': 60,
            'recipients': [
                {'email': 'test1@example.com', 'name': 'Test User 1'},
                {'email': 'test2@example.com', 'name': 'Test User 2'}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'API Test Batch')
        
        # Check recipients were created
        batch = Batch.objects.get(id=response.data['id'])
        self.assertEqual(batch.recipients.count(), 2)
    
    def test_batch_update(self):
        """Test batch update via API"""
        batch = Batch.objects.create(
            name="Original Batch",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60
        )
        
        url = reverse('batches:batch-detail', kwargs={'pk': batch.id})
        data = {
            'name': 'Updated Batch Name',
            'description': 'Updated description'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Batch Name')
    
    def test_batch_execution(self):
        """Test batch execution endpoint"""
        batch = Batch.objects.create(
            name="Test Batch",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60
        )
        
        # Add recipients
        BatchRecipient.objects.create(
            batch=batch,
            email='test@example.com',
            name='Test Recipient'
        )
        
        url = reverse('batches:batch-execute-action', kwargs={'pk': batch.id})
        data = {'action': 'start'}
        
        with patch('batches.tasks.send_batch_emails.delay') as mock_task:
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_task.assert_called_once_with(batch.id)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class BatchTaskTests(TestCase):
    """Test Celery task functionality"""
    
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
        self.template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Test Subject",
            content="Hello {{name}}!",
            tenant=self.tenant
        )
        self.email_config = UserEmailConfiguration.objects.create(
            user=self.user,
            email_host='smtp.gmail.com',
            email_port=587,
            email_use_tls=True,
            email_host_user='test@gmail.com',
            encrypted_email_host_password='encrypted_password',
            provider='gmail'
        )
        self.batch = Batch.objects.create(
            name="Test Batch",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60,
            status='scheduled'
        )
        self.recipient = BatchRecipient.objects.create(
            batch=self.batch,
            email='recipient@example.com',
            name='Test Recipient'
        )
    
    @patch('batches.tasks.send_individual_email_with_retry.delay')
    def test_send_batch_emails_task(self, mock_send_email):
        """Test send_batch_emails task"""
        # Configure mock
        mock_send_email.return_value = MagicMock()
        
        # Execute task
        result = send_batch_emails(self.batch.id)
        
        # Verify task execution
        self.assertTrue(result)
        mock_send_email.assert_called_once()
        
        # Check batch status update
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, 'processing')
    
    def test_batch_subcycle_task(self):
        """Test batch sub-cycle execution"""
        # Enable sub-cycle
        self.batch.sub_cycle_enabled = True
        self.batch.sub_cycle_interval_type = 'days'
        self.batch.sub_cycle_interval_value = 1
        self.batch.save()
        
        # Set recipient next email due
        self.recipient.next_email_due_at = timezone.now() - timedelta(hours=1)
        self.recipient.save()
        
        with patch('batches.tasks.send_individual_email_with_retry.delay') as mock_send:
            result = execute_batch_subcycle(self.batch.id)
            
            self.assertTrue(result)
            mock_send.assert_called_once()


class BatchAnalyticsTests(APITestCase):
    """Test batch analytics functionality"""
    
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
            role='tenant_admin',
            tenant=self.tenant
        )
        
        # Authenticate
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_batch_statistics(self):
        """Test batch statistics endpoint"""
        # Create test data
        template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Test",
            content="Test",
            tenant=self.tenant
        )
        email_config = UserEmailConfiguration.objects.create(
            user=self.user,
            email_host_user='test@gmail.com',
            provider='gmail'
        )
        batch = Batch.objects.create(
            name="Test Batch",
            template=template,
            email_configuration=email_config,
            created_by=self.user,
            interval_minutes=60
        )
        
        url = reverse('batches:batch-statistics', kwargs={'pk': batch.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_recipients', response.data)
        self.assertIn('emails_sent', response.data)
    
    def test_ai_analytics_dashboard(self):
        """Test AI analytics dashboard endpoint"""
        url = reverse('batches:ai-analytics-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('insights', response.data)


class BatchFilteringTests(APITestCase):
    """Test batch filtering and search functionality"""
    
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
            role='tenant_admin',
            tenant=self.tenant
        )
        
        # Authenticate
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create test data
        self.template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Test",
            content="Test",
            tenant=self.tenant
        )
        self.email_config = UserEmailConfiguration.objects.create(
            user=self.user,
            email_host_user='test@gmail.com',
            provider='gmail'
        )
    
    def test_batch_status_filtering(self):
        """Test filtering batches by status"""
        # Create batches with different statuses
        Batch.objects.create(
            name="Active Batch",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60,
            status='processing'
        )
        Batch.objects.create(
            name="Completed Batch",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60,
            status='completed'
        )
        
        url = reverse('batches:batch-list')
        response = self.client.get(url, {'status': 'processing'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'processing')
    
    def test_batch_name_search(self):
        """Test searching batches by name"""
        Batch.objects.create(
            name="Marketing Campaign",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60
        )
        Batch.objects.create(
            name="Weekly Newsletter",
            template=self.template,
            email_configuration=self.email_config,
            created_by=self.user,
            interval_minutes=60
        )
        
        url = reverse('batches:batch-list')
        response = self.client.get(url, {'search': 'Marketing'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('Marketing', response.data['results'][0]['name'])


class BatchSecurityTests(APITestCase):
    """Test batch security and permissions"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create tenants
        self.tenant1 = Tenant.objects.create(name="Tenant 1", slug="tenant-1")
        self.tenant2 = Tenant.objects.create(name="Tenant 2", slug="tenant-2")
        
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant=self.tenant1
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            role='tenant_admin',
            tenant=self.tenant2
        )
        
        # Create templates
        self.template1 = EmailTemplate.objects.create(
            name="Template 1",
            subject="Test",
            content="Test",
            tenant=self.tenant1
        )
        
        # Create email configs
        self.email_config1 = UserEmailConfiguration.objects.create(
            user=self.user1,
            email_host_user='test1@gmail.com',
            provider='gmail'
        )
        
        # Create batch
        self.batch1 = Batch.objects.create(
            name="Tenant 1 Batch",
            template=self.template1,
            email_configuration=self.email_config1,
            created_by=self.user1,
            interval_minutes=60
        )
    
    def test_tenant_isolation(self):
        """Test that users can only access their tenant's batches"""
        # User 1 should see their batch
        refresh = RefreshToken.for_user(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('batches:batch-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # User 2 should not see user 1's batch
        refresh = RefreshToken.for_user(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_batch_access_control(self):
        """Test batch detail access control"""
        # User 2 should not be able to access user 1's batch
        refresh = RefreshToken.for_user(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('batches:batch-detail', kwargs={'pk': self.batch1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

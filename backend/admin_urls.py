from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets from different apps that super admin should access
from tenants.views import TenantViewSet, TenantEmailViewSet, TenantMailSecretViewSet
from batches.views import BatchViewSet
from emails.views import EmailTemplateViewSet
from logs.views import EmailLogViewSet, BatchExecutionEmailLogViewSet
from core.views import (
    UserListView, UserDetailView, user_dashboard, 
    get_user_filter_options, get_available_user_roles
)

# Import super admin specific ViewSets
from tenants.admin_views import (
    SuperAdminGroupViewSet, SuperAdminGroupEmailViewSet
)
from core.views_recipients import ContactGroupViewSet, RecipientViewSet

# Create router for super admin endpoints
router = DefaultRouter()

# Super admin gets global access to all resources
router.register(r'tenants', TenantViewSet, basename='admin-tenant')
router.register(r'tenant-emails', TenantEmailViewSet, basename='admin-tenant-email')
router.register(r'tenant-mail-secrets', TenantMailSecretViewSet, basename='admin-tenant-mail-secret')
router.register(r'groups', SuperAdminGroupViewSet, basename='admin-group')
router.register(r'group-emails', SuperAdminGroupEmailViewSet, basename='admin-group-email')
router.register(r'batches', BatchViewSet, basename='admin-batch')
router.register(r'email-templates', EmailTemplateViewSet, basename='admin-email-template')
router.register(r'email-logs', EmailLogViewSet, basename='admin-email-log')
router.register(r'batch-execution-logs', BatchExecutionEmailLogViewSet, basename='admin-batch-execution-log')
router.register(r'contact-groups', ContactGroupViewSet, basename='admin-contact-group')
router.register(r'recipients', RecipientViewSet, basename='admin-recipient')

urlpatterns = [
    # Include all the router URLs
    path('', include(router.urls)),
    
    # User management endpoints for super admin
    path('users/', UserListView.as_view(), name='admin-user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='admin-user-detail'),
    path('users/filter-options/', get_user_filter_options, name='admin-user-filter-options'),
    path('users/available-roles/', get_available_user_roles, name='admin-user-available-roles'),
    path('dashboard/', user_dashboard, name='admin-dashboard'),
]
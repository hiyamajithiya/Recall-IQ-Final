from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantViewSet, TenantEmailViewSet, TenantMailSecretViewSet, 
    TenantAdminGroupViewSet, TenantStaffGroupViewSet, GroupViewSet,
    TenantAdminGroupEmailViewSet, TenantStaffGroupEmailViewSet, GroupEmailViewSet,
    TenantAdminBatchViewSet, TenantStaffBatchViewSet,
    TenantAdminRecipientViewSet, TenantStaffRecipientViewSet,
    TenantAdminContactGroupViewSet, TenantStaffContactGroupViewSet
)
from .admin_views import SuperAdminTenantViewSet

router = DefaultRouter()

# Super admin endpoints
router.register(r'super-admin/tenants', SuperAdminTenantViewSet, basename='super-admin-tenant')

# Register specific endpoints BEFORE the empty pattern to avoid conflicts
# New role-based endpoints
router.register(r'admin/groups', TenantAdminGroupViewSet, basename='tenant-admin-group')
router.register(r'admin/group-emails', TenantAdminGroupEmailViewSet, basename='tenant-admin-group-email')
router.register(r'admin/recipients', TenantAdminRecipientViewSet, basename='tenant-admin-recipient')
router.register(r'admin/contact-groups', TenantAdminContactGroupViewSet, basename='tenant-admin-contact-group')
router.register(r'admin/batches', TenantAdminBatchViewSet, basename='tenant-admin-batch')
router.register(r'staff/groups', TenantStaffGroupViewSet, basename='tenant-staff-group')
router.register(r'staff/group-emails', TenantStaffGroupEmailViewSet, basename='tenant-staff-group-email')
router.register(r'staff/recipients', TenantStaffRecipientViewSet, basename='tenant-staff-recipient')
router.register(r'staff/contact-groups', TenantStaffContactGroupViewSet, basename='tenant-staff-contact-group')
router.register(r'staff/batches', TenantStaffBatchViewSet, basename='tenant-staff-batch')

# Legacy endpoints for backward compatibility
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'group-emails', GroupEmailViewSet, basename='group-email')
# Fallback recipients endpoint - uses TenantAdminRecipientViewSet for compatibility
router.register(r'recipients', TenantAdminRecipientViewSet, basename='legacy-recipient')
router.register(r'contact-groups', TenantAdminContactGroupViewSet, basename='legacy-contact-group')

# Register these AFTER specific endpoints to avoid URL conflicts
router.register(r'emails', TenantEmailViewSet, basename='tenant-email')
router.register(r'mail-secrets', TenantMailSecretViewSet, basename='tenant-mail-secret')
# Empty pattern should be LAST to avoid catching everything
router.register(r'', TenantViewSet, basename='tenant')

urlpatterns = [
    path('', include(router.urls)),
]
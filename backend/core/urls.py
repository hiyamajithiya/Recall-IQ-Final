from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    TenantAdminRegistrationView,
    google_oauth_signup,
    password_reset_request,
    password_reset_confirm,
    request_signup_otp,
    verify_signup_otp,
    UserProfileView,
    UserListView,
    UserDetailView,
    UserEmailConfigurationViewSet,
    UserEmailConfigurationDetailView,
    user_dashboard,
    change_password,
    test_email_configuration,
    test_email_settings,
    get_default_email_configuration,
    debug_welcome_email,
    debug_user_visibility,
    fix_email_config_password,
    check_email_config_health,
    get_user_filter_options,
    get_available_user_roles,
    get_tenant_email_configurations,
    health_check,
    detailed_health_check,
    admin_redirect_view,
    admin_login_redirect_view
)
from .dashboard_views import tenant_dashboard
from .views_recipients import ContactGroupViewSet, RecipientViewSet

# Set up the router
router = DefaultRouter()
router.register(r'contact-groups', ContactGroupViewSet, basename='contact-group')
router.register(r'recipients', RecipientViewSet, basename='recipient')

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegistrationView.as_view(), name='user_register'),
    path('tenant-admin-register/', TenantAdminRegistrationView.as_view(), name='tenant_admin_register'),
    path('google-oauth-signup/', google_oauth_signup, name='google_oauth_signup'),
    path('password-reset-request/', password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/', password_reset_confirm, name='password_reset_confirm'),
    path('request-signup-otp/', request_signup_otp, name='request_signup_otp'),
    path('verify-signup-otp/', verify_signup_otp, name='verify_signup_otp'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', change_password, name='change_password'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('email-configurations/', UserEmailConfigurationViewSet.as_view(), name='email_configurations'),
    path('email-configurations/<int:pk>/', UserEmailConfigurationDetailView.as_view(), name='email_configuration_detail'),
    path('email-configurations/<int:config_id>/test/', test_email_configuration, name='test_email_configuration'),
    path('email-configurations/test-settings/', test_email_settings, name='test_email_settings'),
    path('email-configurations/default/', get_default_email_configuration, name='default_email_configuration'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
    path('tenant-dashboard/', tenant_dashboard, name='tenant_dashboard'),
    path('debug/welcome-email/', debug_welcome_email, name='debug_welcome_email'),
    path('debug/user-visibility/', debug_user_visibility, name='debug_user_visibility'),
    path('debug/fix-email-config/', fix_email_config_password, name='fix_email_config_password'),
    path('email-configurations/health/', check_email_config_health, name='check_email_config_health'),
    path('users/filter-options/', get_user_filter_options, name='get_user_filter_options'),
    path('users/available-roles/', get_available_user_roles, name='get_available_user_roles'),
    path('tenant-email-configurations/', get_tenant_email_configurations, name='get_tenant_email_configurations'),
    
    # Health monitoring endpoints
    path('health/', health_check, name='health_check'),
    path('health/detailed/', detailed_health_check, name='detailed_health_check'),
    
    # Include the router URLs
    path('', include(router.urls)),
]
"""
RecallIQ URL Configuration
Enterprise-grade API routing with documentation and health monitoring
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.views import admin_redirect_view, admin_login_redirect_view

admin.site.site_header = "RecallIQ Admin"
admin.site.site_title = "RecallIQ"
admin.site.index_title = "RecallIQ Administration"

# API Documentation URLs
api_docs_patterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

urlpatterns = [
    # Admin interface - redirect to React app
    path('admin/login/', admin_login_redirect_view, name='admin_login_redirect'),
    path('admin/', admin_redirect_view, name='admin_redirect'),
    
    # Keep Django admin available at different URL for emergency access
    path('django-admin/', admin.site.urls),
    
    # API Documentation
    path('api/', include(api_docs_patterns)),
    
    # Core API endpoints
    path('api/auth/', include('core.urls')),
    path('api/admin/', include('admin_urls')),  # Super admin global endpoints
    path('api/tenants/', include('tenants.urls')),
    path('api/emails/', include('emails.urls')),
    path('api/batches/', include('batches.urls')),
    path('api/logs/', include('logs.urls')),
    
    # Health monitoring endpoints (handled by core app)
    # path('health/', include('core.health_urls')),  # Moved to core.urls
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BatchViewSet, TenantAdminBatchViewSet, TenantStaffBatchViewSet,
    duplicate_batch, pause_batch, resume_batch, cancel_batch,
    batch_analytics_summary, batch_dashboard_overview
)
from . import ai_views
from .api_views import process_scheduled_batches, process_specific_batch, fix_batch_recipients
# TODO: Re-enable when bulk_operations and recipient_filtering modules are restored
# from . import bulk_operations, recipient_filtering

router = DefaultRouter()

# Role-based endpoints for batches
router.register(r'admin', TenantAdminBatchViewSet, basename='tenant-admin-batch')
router.register(r'staff', TenantStaffBatchViewSet, basename='tenant-staff-batch')

# Default endpoint for backward compatibility and super admin
router.register(r'', BatchViewSet, basename='batch')

urlpatterns = [
    path('', include(router.urls)),
    
    # 🔄 Batch Processing API Endpoints
    path('process-scheduled/', process_scheduled_batches, name='process-scheduled-batches'),
    path('<int:batch_id>/process/', process_specific_batch, name='process-specific-batch'),
    path('fix-recipients/', fix_batch_recipients, name='fix-batch-recipients'),
    
    # 🤖 AI-Powered Analytics Endpoints - Phase 2
    path('ai-analytics/dashboard/', ai_views.get_ai_analytics_dashboard, name='ai-analytics-dashboard'),
    path('ai-analytics/optimal-send-times/', ai_views.get_optimal_send_times, name='optimal-send-times'),
    path('ai-analytics/engagement-patterns/', ai_views.get_recipient_engagement_patterns, name='engagement-patterns'),
    path('ai-analytics/predict-success/', ai_views.predict_batch_success, name='predict-batch-success'),
    path('ai-analytics/analyze-domains/', ai_views.analyze_recipient_domains, name='analyze-domains'),
    path('ai-analytics/performance-trends/', ai_views.get_batch_performance_trends, name='performance-trends'),
    path('ai-analytics/recommendations/', ai_views.get_ai_recommendations, name='ai-recommendations'),
    path('ai-analytics/real-time-insights/', ai_views.get_real_time_insights, name='real-time-insights'),
    
    # 🚀 Enhanced Batch Management - Phase 4
    path('<int:batch_id>/duplicate/', duplicate_batch, name='duplicate-batch'),
    path('<int:batch_id>/pause/', pause_batch, name='pause-batch'),
    path('<int:batch_id>/resume/', resume_batch, name='resume-batch'),
    path('<int:batch_id>/cancel/', cancel_batch, name='cancel-batch'),
    path('<int:batch_id>/analytics/', batch_analytics_summary, name='batch-analytics'),
    path('dashboard/overview/', batch_dashboard_overview, name='dashboard-overview'),
    
    # TODO: Re-enable bulk operations and recipient filtering when modules are restored
    # 🔄 Bulk Recipient Operations - Phase 4
    # path('<int:batch_id>/recipients/bulk-actions/', bulk_operations.bulk_recipient_actions, name='bulk-recipient-actions'),
    # path('<int:batch_id>/recipients/import-csv/', bulk_operations.import_recipients_csv, name='import-recipients-csv'),
    # path('<int:batch_id>/recipients/export-csv/', bulk_operations.export_recipients_csv, name='export-recipients-csv'),
    # path('<int:batch_id>/recipients/analytics/', bulk_operations.recipient_analytics, name='recipient-analytics'),
    
    # 🔍 Advanced Recipient Filtering - Phase 4
    # path('<int:batch_id>/recipients/search/', recipient_filtering.advanced_recipient_search, name='advanced-recipient-search'),
    # path('<int:batch_id>/recipients/quick-filters/', recipient_filtering.recipient_quick_filters, name='recipient-quick-filters'),
    # path('<int:batch_id>/recipients/save-filter/', recipient_filtering.save_recipient_filter, name='save-recipient-filter'),
    # path('<int:batch_id>/recipients/data-quality/', recipient_filtering.recipient_data_quality, name='recipient-data-quality'),
]
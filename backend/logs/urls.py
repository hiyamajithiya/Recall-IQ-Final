from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmailLogViewSet, BatchExecutionEmailLogViewSet, test_analytics_api

router = DefaultRouter()
router.register(r'emails', EmailLogViewSet, basename='email-log')
router.register(r'batch-executions', BatchExecutionEmailLogViewSet, basename='batch-execution-log')

urlpatterns = [
    path('', include(router.urls)),
    path('test-analytics/', test_analytics_api, name='test-analytics'),
]
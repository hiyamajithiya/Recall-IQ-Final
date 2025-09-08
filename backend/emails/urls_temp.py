from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmailTemplateViewSet, EmailConfigurationViewSet

router = DefaultRouter()
router.register(r'templates', EmailTemplateViewSet, basename='emailtemplate')
router.register(r'configurations', EmailConfigurationViewSet, basename='emailconfiguration')

urlpatterns = [
    path('', include(router.urls)),
]

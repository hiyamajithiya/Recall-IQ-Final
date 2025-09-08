from django.db import models
from django.conf import settings
from tenants.models import Tenant

class ContactGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='contact_groups')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'tenant')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

class Recipient(models.Model):
    name = models.CharField(max_length=150)
    organization_name = models.CharField(max_length=200)
    email = models.EmailField()
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='recipients')
    groups = models.ManyToManyField(ContactGroup, related_name='recipients', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('email', 'tenant')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.email})"

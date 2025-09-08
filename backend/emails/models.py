from django.db import models
from django.utils import timezone
from tenants.models import Tenant


class EmailTemplate(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='email_templates')
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    is_html = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_templates'
        unique_together = ['tenant', 'name']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.name}"


class GroupEmail(models.Model):
    # ...existing fields...
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    # ...existing fields...
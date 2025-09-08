from django.contrib import admin
from .models import EmailTemplate


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'name', 'subject', 'is_html', 'is_active', 'created_at']
    list_filter = ['tenant', 'is_html', 'is_active', 'created_at']
    search_fields = ['name', 'subject']
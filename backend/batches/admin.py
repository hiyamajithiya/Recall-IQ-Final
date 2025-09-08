from django.contrib import admin
from .models import Batch, BatchGroup, BatchRecord


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'name', 'template', 'status', 'start_time', 'total_recipients', 'emails_sent', 'created_at']
    list_filter = ['tenant', 'status', 'created_at', 'start_time']
    search_fields = ['name', 'description']
    readonly_fields = ['total_recipients', 'emails_sent', 'emails_failed']


@admin.register(BatchGroup)
class BatchGroupAdmin(admin.ModelAdmin):
    list_display = ['batch', 'group', 'created_at']
    list_filter = ['batch__tenant', 'created_at']


@admin.register(BatchRecord)
class BatchRecordAdmin(admin.ModelAdmin):
    list_display = ['batch', 'recipient_email', 'recipient_name', 'document_received', 'marked_done', 'created_at']
    list_filter = ['batch__tenant', 'document_received', 'marked_done', 'created_at']
    search_fields = ['recipient_email', 'recipient_name']
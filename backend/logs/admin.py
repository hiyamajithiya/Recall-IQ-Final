from django.contrib import admin
from .models import EmailLog, BatchExecutionEmailLog


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'email_type', 'from_email', 'to_email', 'status', 'sent_at', 'created_at']
    list_filter = ['tenant', 'email_type', 'status', 'created_at', 'sent_at']
    search_fields = ['from_email', 'to_email', 'subject']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BatchExecutionEmailLog)
class BatchExecutionEmailLogAdmin(admin.ModelAdmin):
    list_display = ['batch', 'email_log', 'execution_sequence', 'created_at']
    list_filter = ['batch__tenant', 'created_at']
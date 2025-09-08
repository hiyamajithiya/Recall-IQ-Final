from rest_framework import serializers
from .models import EmailLog, BatchExecutionEmailLog


class EmailLogSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    documents_received_by_email = serializers.CharField(source='documents_received_by.email', read_only=True)
    
    class Meta:
        model = EmailLog
        fields = [
            'id', 'tenant', 'tenant_name', 'batch', 'batch_name', 'batch_recipient',
            'email_type', 'status', 'direction', 'from_email', 'to_email', 
            'subject', 'body', 'error_message', 'metadata',
            'documents_received', 'documents_received_at', 'documents_received_by', 
            'documents_received_by_email', 'sent_at', 'delivered_at', 'opened_at', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'documents_received_by', 'documents_received_at',
            'created_at', 'updated_at'
        ]


class BatchExecutionEmailLogSerializer(serializers.ModelSerializer):
    email_log = EmailLogSerializer(read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    
    class Meta:
        model = BatchExecutionEmailLog
        fields = ['id', 'batch', 'batch_name', 'email_log', 'execution_sequence', 'created_at']
        read_only_fields = ['id', 'created_at']


class EmailLogFilterSerializer(serializers.Serializer):
    email_type = serializers.ChoiceField(
        choices=EmailLog.EMAIL_TYPE_CHOICES,
        required=False
    )
    status = serializers.ChoiceField(
        choices=EmailLog.STATUS_CHOICES,
        required=False
    )
    from_email = serializers.EmailField(required=False)
    to_email = serializers.EmailField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    search = serializers.CharField(required=False, max_length=255)
    documents_received = serializers.BooleanField(required=False)
    batch_id = serializers.IntegerField(required=False)


class EmailLogStatsSerializer(serializers.Serializer):
    total_emails = serializers.IntegerField()
    sent_emails = serializers.IntegerField()
    failed_emails = serializers.IntegerField()
    pending_emails = serializers.IntegerField()
    success_rate = serializers.FloatField()
    by_type = serializers.DictField()
    by_status = serializers.DictField()
    recent_activity = serializers.ListField()
from rest_framework import serializers
from .models import EmailTemplate


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = ['id', 'tenant', 'name', 'subject', 'body', 'is_html', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']  # Make tenant read-only
    
    def validate(self, data):
        print(f"DEBUG: Validating template data: {data}")
        return data
    
    def validate_name(self, value):
        print(f"DEBUG: Validating name: {value}")
        tenant = self.context['request'].user.tenant
        print(f"DEBUG: User tenant: {tenant}")
        
        if tenant and self.instance:
            existing = EmailTemplate.objects.filter(
                tenant=tenant,
                name=value
            ).exclude(id=self.instance.id).exists()
        elif tenant:
            existing = EmailTemplate.objects.filter(
                tenant=tenant,
                name=value
            ).exists()
        else:
            existing = False
        
        print(f"DEBUG: Existing template with name '{value}': {existing}")
        
        if existing:
            raise serializers.ValidationError("Template with this name already exists for your tenant.")
        
        return value


class EmailTemplatePreviewSerializer(serializers.Serializer):
    subject = serializers.CharField()
    body = serializers.CharField()
    template_variables = serializers.JSONField(default=dict)
    recipient_name = serializers.CharField(default="John Doe")
    recipient_email = serializers.EmailField(default="john.doe@example.com")
    
    def validate(self, data):
        return data
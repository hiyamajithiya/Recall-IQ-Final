from rest_framework import serializers
from .models import Tenant
from django.utils import timezone

class SuperAdminTenantSerializer(serializers.ModelSerializer):
    """
    Serializer for super admin to create and manage tenants
    """
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'logo', 'plan', 'status', 'subscription_start_date',
            'subscription_end_date', 'trial_end_date', 'monthly_email_limit',
            'emails_sent_this_month', 'company_address', 'contact_person',
            'contact_email', 'contact_phone', 'billing_email', 'payment_method',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'emails_sent_this_month', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Custom validation for tenant data"""
        # Required fields validation
        required_fields = ['name', 'company_address', 'contact_person', 'contact_email', 'contact_phone']
        for field in required_fields:
            if not self.instance and field not in attrs:
                raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})

        # Validate name uniqueness
        name = attrs.get('name')
        if name:
            existing = Tenant.objects.filter(name=name)
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError({'name': 'A tenant with this name already exists'})

        # Auto-fill billing email if not provided
        if 'contact_email' in attrs and not attrs.get('billing_email'):
            attrs['billing_email'] = attrs['contact_email']

        # Validate dates
        now = timezone.now()
        subscription_start_date = attrs.get('subscription_start_date')
        subscription_end_date = attrs.get('subscription_end_date')
        trial_end_date = attrs.get('trial_end_date')

        if subscription_start_date and subscription_end_date:
            if subscription_end_date <= subscription_start_date:
                raise serializers.ValidationError({
                    'subscription_end_date': 'Subscription end date must be after subscription start date'
                })

        if trial_end_date and subscription_start_date:
            if subscription_start_date < trial_end_date:
                raise serializers.ValidationError({
                    'subscription_start_date': 'Subscription start date should be equal to or after trial end date'
                })

        # Plan validation
        plan = attrs.get('plan', self.instance.plan if self.instance else 'starter')
        if plan not in dict(Tenant.PLAN_CHOICES):
            raise serializers.ValidationError({'plan': 'Invalid plan selected'})

        # Status validation
        status = attrs.get('status', self.instance.status if self.instance else 'trial')
        if status not in dict(Tenant.STATUS_CHOICES):
            raise serializers.ValidationError({'status': 'Invalid status selected'})

        return attrs

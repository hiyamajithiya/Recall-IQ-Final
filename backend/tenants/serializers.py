from rest_framework import serializers
from .models import Tenant, TenantEmail, Group, TenantMailSecret, GroupEmail
import openpyxl
from io import BytesIO


class TenantSerializer(serializers.ModelSerializer):
    days_until_expiry = serializers.ReadOnlyField()
    email_usage_percentage = serializers.ReadOnlyField()
    emails_sent_this_month_countable = serializers.ReadOnlyField()
    is_subscription_active = serializers.ReadOnlyField()
    is_trial_active = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    expires_soon = serializers.ReadOnlyField()
    
    # User limit computed fields
    current_user_counts = serializers.ReadOnlyField()
    users_remaining = serializers.ReadOnlyField()
    user_usage_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'logo', 'plan', 'status', 'subscription_start_date',
            'subscription_end_date', 'trial_end_date', 'monthly_email_limit',
            'emails_sent_this_month', 'company_address', 'contact_person',
            'contact_email', 'contact_phone', 'billing_email', 'payment_method',
            # User limits - manually configured
            'max_tenant_admins', 'max_staff_admins', 'max_staff_users', 'max_total_users',
            'is_active', 'created_at', 'updated_at',
            # Read-only computed fields
            'days_until_expiry', 'email_usage_percentage', 'emails_sent_this_month_countable',
            'is_subscription_active', 'is_trial_active', 'is_expired', 'expires_soon',
            # User limit computed fields
            'current_user_counts', 'users_remaining', 'user_usage_percentage'
        ]
        read_only_fields = ['trial_end_date']

    def validate(self, attrs):
        """Custom validation for tenant data"""
        from django.utils import timezone

        now = timezone.now()

        # Required fields only for creation
        required_fields = ['company_address', 'contact_person', 'contact_email', 'contact_phone']
        for field in required_fields:
            if not self.instance and field in attrs and not attrs[field]:
                raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required"})

        # Auto-fill billing email if not provided
        if 'contact_email' in attrs and not attrs.get('billing_email'):
            attrs['billing_email'] = attrs['contact_email']

        # Dates from request
        subscription_start_date = attrs.get('subscription_start_date')
        subscription_end_date = attrs.get('subscription_end_date')

        # Dates from existing object (for updates)
        existing_start = self.instance.subscription_start_date if self.instance else None
        existing_end = self.instance.subscription_end_date if self.instance else None
        trial_end_date = self.instance.trial_end_date if self.instance else None

        # --- Trial end date vs subscription start date ---
        if trial_end_date and subscription_start_date:
            # Only check if creating or actually changing start date
            if not self.instance or subscription_start_date != existing_start:
                if subscription_start_date < trial_end_date:
                    raise serializers.ValidationError({
                        'subscription_start_date': 'Subscription start date should be equal to or after trial end date'
                    })

        # --- Start date not in the past (only for creation, not updates) ---
        if subscription_start_date and not self.instance:
            if subscription_start_date < now:
                raise serializers.ValidationError({
                    'subscription_start_date': 'Subscription start date cannot be in the past'
                })

        # --- End date after start date ---
        start_date_to_check = subscription_start_date or existing_start
        if subscription_end_date and start_date_to_check:
            if subscription_end_date <= start_date_to_check:
                raise serializers.ValidationError({
                    'subscription_end_date': 'Subscription end date must be after subscription start date'
                })

        # --- User Limits Validation ---
        max_tenant_admins = attrs.get('max_tenant_admins', 1)
        max_staff_admins = attrs.get('max_staff_admins', 1)
        max_staff_users = attrs.get('max_staff_users', 3)
        max_total_users = attrs.get('max_total_users', 5)

        # Minimum requirements
        if max_tenant_admins < 1:
            raise serializers.ValidationError({
                'max_tenant_admins': 'Must have at least 1 tenant admin'
            })

        if max_total_users < 1:
            raise serializers.ValidationError({
                'max_total_users': 'Must have at least 1 total user'
            })

        # Total users should be >= sum of individual role limits
        min_required_total = max_tenant_admins + max_staff_admins + max_staff_users
        if max_total_users < min_required_total:
            raise serializers.ValidationError({
                'max_total_users': f'Total users ({max_total_users}) must be at least {min_required_total} '
                                  f'(sum of tenant admins + staff admins + staff users)'
            })

        # If updating existing tenant, check current usage doesn't exceed new limits
        if self.instance:
            current_counts = self.instance.current_user_counts
            
            if current_counts['tenant_admin'] > max_tenant_admins:
                raise serializers.ValidationError({
                    'max_tenant_admins': f'Cannot set limit to {max_tenant_admins}. '
                                       f'Currently has {current_counts["tenant_admin"]} tenant admin(s)'
                })
            
            if current_counts['staff_admin'] > max_staff_admins:
                raise serializers.ValidationError({
                    'max_staff_admins': f'Cannot set limit to {max_staff_admins}. '
                                      f'Currently has {current_counts["staff_admin"]} staff admin(s)'
                })
            
            if (current_counts['staff'] + current_counts['sales_team']) > max_staff_users:
                raise serializers.ValidationError({
                    'max_staff_users': f'Cannot set limit to {max_staff_users}. '
                                     f'Currently has {current_counts["staff"] + current_counts["sales_team"]} staff user(s)'
                })
            
            if current_counts['total'] > max_total_users:
                raise serializers.ValidationError({
                    'max_total_users': f'Cannot set limit to {max_total_users}. '
                                     f'Currently has {current_counts["total"]} total user(s)'
                })

        return attrs


class TenantEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantEmail
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    email_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Group
        fields = ['id', 'tenant', 'name', 'description', 'is_active', 'created_at', 'updated_at', 'email_count']
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at', 'email_count']


class TenantMailSecretSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantMailSecret
        fields = '__all__'
        extra_kwargs = {
            'encrypted_password': {'write_only': True},
            'encrypted_client_secret': {'write_only': True},
        }


class GroupEmailModelSerializer(serializers.ModelSerializer):
    """ModelSerializer for individual GroupEmail objects (for ViewSets)"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = GroupEmail
        fields = ['id', 'group', 'email', 'name', 'company', 'is_active', 'created_at', 'group_name']
        read_only_fields = ['id', 'created_at', 'group_name']


class GroupEmailSerializer(serializers.Serializer):
    """Serializer for bulk adding emails to groups"""
    emails = serializers.ListField(
        child=serializers.EmailField(),
        help_text="List of email addresses to add"
    )
    names = serializers.ListField(
        child=serializers.CharField(max_length=100, required=False),
        required=False,
        help_text="Optional list of names corresponding to emails"
    )


class BulkEmailUploadSerializer(serializers.Serializer):
    """Serializer for bulk email upload"""
    contacts = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of contact objects with email, name, organization"
    )
    
    def validate_contacts(self, value):
        """Validate that each contact has at least an email"""
        for contact in value:
            if not contact.get('email'):
                raise serializers.ValidationError("Each contact must have an email address")
            if 'organization' not in contact:
                contact['organization'] = ''
        return value


class ExcelUploadSerializer(serializers.Serializer):
    """Serializer for Excel file upload"""
    file = serializers.FileField(help_text="Excel file containing contacts")
    
    def validate_file(self, value):
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError("File must be an Excel file (.xlsx or .xls)")
        
        try:
            workbook = openpyxl.load_workbook(value, read_only=True)
            worksheet = workbook.active
            
            contacts = []
            for row_num, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                if not row or not any(row):
                    continue
                
                email = row[0] if row[0] else ''
                name = row[1] if len(row) > 1 and row[1] else ''
                organization = row[2] if len(row) > 2 and row[2] else ''
                
                if email and '@' in email:
                    contacts.append({
                        'email': str(email).strip(),
                        'name': str(name).strip() if name else '',
                        'organization': str(organization).strip() if organization else ''
                    })
                elif email:
                    raise serializers.ValidationError(f"Invalid email format in row {row_num}: {email}")
            
            if not contacts:
                raise serializers.ValidationError("No valid contacts found in the Excel file")
                
            workbook.close()
            return contacts
            
        except openpyxl.utils.exceptions.InvalidFileException:
            raise serializers.ValidationError("Invalid Excel file format")
        except Exception as e:
            raise serializers.ValidationError(f"Error reading Excel file: {str(e)}")

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth import authenticate
from .models import User, UserEmailConfiguration
from tenants.models import Tenant


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Override default fields to use 'login' instead of 'username'
    username = None  # Remove default username field
    login = serializers.CharField(required=True)  # Field to accept either username or email
    password = serializers.CharField(required=True, write_only=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the username field from parent class
        if 'username' in self.fields:
            del self.fields['username']
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['tenant_id'] = user.tenant.id if user.tenant else None
        token['tenant_name'] = user.tenant.name if user.tenant else None
        return token
    
    def validate(self, attrs):
        login = attrs.get('login')
        password = attrs.get('password')
        
        # Try to find user by email or username using the helper method
        user = User.get_by_login(login)
        if not user:
            raise serializers.ValidationError({
                'login': 'No account found with the given username or email'
            })
        
        # Authenticate with username and password
        if not user.check_password(password):
            raise serializers.ValidationError({
                'password': 'Invalid password'
            })
        
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')
            
        # Generate token
        refresh = self.get_token(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'tenant_id': user.tenant.id if user.tenant else None,
                'tenant_name': user.tenant.name if user.tenant else None,
            }
        }
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'role', 'tenant']
        extra_kwargs = {
            'role': {'read_only': True},
            'tenant': {'read_only': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class TenantAdminRegistrationSerializer(serializers.ModelSerializer):
    # User fields
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    # Tenant fields
    company_name = serializers.CharField(max_length=255)
    company_address = serializers.CharField()
    contact_person = serializers.CharField(max_length=255)
    contact_email = serializers.EmailField()
    contact_phone = serializers.CharField(max_length=20)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'company_name', 'company_address', 'contact_person', 'contact_email', 'contact_phone'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        
        # Check if contact_email already exists as a user email
        if User.objects.filter(email=attrs['contact_email']).exists():
            raise serializers.ValidationError("Contact email is already registered as a user.")
        
        # Check if company name already exists
        if Tenant.objects.filter(name=attrs['company_name']).exists():
            raise serializers.ValidationError("Company name already exists. Please choose a different name.")
        
        return attrs
    
    def create(self, validated_data):
        from django.utils import timezone
        from datetime import timedelta
        
        # Extract tenant data
        tenant_data = {
            'name': validated_data.pop('company_name'),
            'company_address': validated_data.pop('company_address'),
            'contact_person': validated_data.pop('contact_person'),
            'contact_email': validated_data.pop('contact_email'),
            'contact_phone': validated_data.pop('contact_phone'),
            'status': 'trial',
            'plan': 'starter',
            'trial_end_date': timezone.now() + timedelta(days=14),  # 14-day trial
            'monthly_email_limit': 1000,
        }
        
        # Create tenant
        tenant = Tenant.objects.create(**tenant_data)
        
        # Extract user data
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Create tenant admin user
        validated_data['role'] = 'tenant_admin'
        validated_data['tenant'] = tenant
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(max_length=255)
    
    def validate_username_or_email(self, value):
        # Don't validate if user exists here to prevent email enumeration
        # The view will handle user lookup internally
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=100)
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs


class EmailOTPRequestSerializer(serializers.Serializer):
    # User fields for tenant admin signup
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    password = serializers.CharField(min_length=8)
    password_confirm = serializers.CharField(min_length=8)
    
    # Tenant fields
    company_name = serializers.CharField(max_length=255)
    company_address = serializers.CharField()
    contact_person = serializers.CharField(max_length=255)
    contact_email = serializers.EmailField()
    contact_phone = serializers.CharField(max_length=20)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        
        # Check if username or email already exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("Username already exists.")
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already exists.")
        
        # Check if contact_email already exists
        if User.objects.filter(email=attrs['contact_email']).exists():
            raise serializers.ValidationError("Contact email is already registered as a user.")
        
        # Check if company name already exists
        from tenants.models import Tenant
        if Tenant.objects.filter(name=attrs['company_name']).exists():
            raise serializers.ValidationError("Company name already exists.")
        
        return attrs


class EmailOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_data = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'tenant', 'tenant_name', 'tenant_data', 'created_by', 'created_by_name', 'is_active', 'created_at', 'password']
        read_only_fields = ['id', 'created_at', 'tenant_name', 'tenant_data', 'created_by', 'created_by_name']
    
    def get_tenant_data(self, obj):
        if obj.tenant:
            return {
                'id': obj.tenant.id,
                'name': obj.tenant.name,
                'contact_email': obj.tenant.contact_email,
                'plan': obj.tenant.plan,
                'status': obj.tenant.status
            }
        return None
    
    def validate(self, attrs):
        request_user = self.context.get('request_user')
        if not request_user:
            raise serializers.ValidationError("Request user is required")
        
        # Only apply role creation restrictions for new user creation, not updates
        if not self.instance:  # self.instance is None for creation, set for updates
            role = attrs.get('role')
            tenant = attrs.get('tenant')
            
            # Super admin can create tenant_admin, sales_team, and support_team users
            if request_user.role == 'super_admin':
                if role not in ['tenant_admin', 'sales_team', 'support_team']:
                    raise serializers.ValidationError({
                        'role': 'Super admin can only create tenant admin, sales team, and Support team users'
                    })
                if role == 'tenant_admin' and not tenant:
                    raise serializers.ValidationError({
                        'tenant': 'Tenant is required when creating tenant admin'
                    })
                # Sales team and Support team users don't need a tenant (they operate across all tenants)
                if role in ['sales_team', 'support_team']:
                    attrs['tenant'] = None  # Ensure system-wide roles have no tenant assignment
            
            # Tenant admin and staff admin can create staff_admin and staff users for their own tenant, but NOT tenant_admin or user role
            elif request_user.role in ['tenant_admin', 'staff_admin']:
                if role not in ['staff_admin', 'staff']:
                    raise serializers.ValidationError({
                        'role': 'Tenant admin and staff admin can only create staff admin and staff users'
                    })
                # Automatically assign tenant admin's own tenant if not provided or if provided tenant doesn't match
                if not tenant or tenant != request_user.tenant:
                    attrs['tenant'] = request_user.tenant
            
            # Other roles cannot create users
            else:
                raise serializers.ValidationError({
                    'role': 'You do not have permission to create users'
                })
            
            # Check tenant user limits for new user creation
            if tenant:  # Only check limits if user has a tenant
                can_add, message = tenant.can_add_user(role)
                if not can_add:
                    raise serializers.ValidationError({
                        'role': f'Cannot create {role}: {message}'
                    })
        
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        
        # Set created_by from context
        request_user = self.context.get('request_user')
        if request_user:
            validated_data['created_by'] = request_user
        
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        # Check permissions for updating user
        request_user = self.context.get('request_user')
        if request_user:
            # Tenant admin and staff admin can only modify users in their own tenant
            if (request_user.role in ['tenant_admin', 'staff_admin'] and 
                instance.tenant != request_user.tenant):
                raise serializers.ValidationError({
                    'non_field_errors': 'You can only modify users in your own tenant'
                })
        
        # Don't update password through regular profile update
        validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        return user


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        
    def validate_email(self, value):
        user = self.instance
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class UserEmailConfigurationSerializer(serializers.ModelSerializer):
    email_host_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = UserEmailConfiguration
        fields = [
            'id', 'name', 'provider', 'email_host', 'email_port', 'email_use_tls', 
            'email_use_ssl', 'email_host_user', 'email_host_password', 'from_email', 
            'from_name', 'is_active', 'is_default', 'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_verified']
    
    def validate(self, attrs):
        """Validate based on provider type"""
        provider = attrs.get('provider')
        
        # OAuth providers don't need SMTP fields
        if provider in ['gmail', 'outlook']:
            # OAuth providers - clear SMTP fields
            smtp_fields = ['email_host', 'email_port', 'email_use_tls', 'email_use_ssl', 'email_host_user']
            for field in smtp_fields:
                attrs.pop(field, None)
        else:
            # SMTP providers - require SMTP fields
            required_fields = ['email_host', 'email_host_user', 'from_email']
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({field: f'{field} is required for SMTP providers.'})
            
            # Password is required for new SMTP configurations
            if not self.instance and not attrs.get('email_host_password'):
                raise serializers.ValidationError({'email_host_password': 'Password is required for new SMTP configurations.'})
        
        return attrs
    
    def validate_name(self, value):
        """Check for unique name per user, excluding current instance during updates"""
        user = self.context['request'].user
        queryset = UserEmailConfiguration.objects.filter(user=user, name=value)
        
        # Exclude current instance during updates
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError("A configuration with this name already exists.")
        
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('email_host_password', '')
        config = UserEmailConfiguration.objects.create(**validated_data)
        
        if password:
            try:
                config.encrypt_password(password)
                config.save()
                
                # Verify the encryption worked by testing decryption
                test_decrypt = config.decrypt_password()
                if not test_decrypt:
                    # Clean up the created config if encryption failed
                    config.delete()
                    raise serializers.ValidationError({
                        'email_host_password': 'Password encryption failed. Please check your system configuration and try again.'
                    })
                elif test_decrypt != password:
                    # Clean up the created config if encryption validation failed
                    config.delete()
                    raise serializers.ValidationError({
                        'email_host_password': 'Password encryption validation failed. Please contact system administrator.'
                    })
                    
            except Exception as e:
                # Clean up the created config if any error occurred
                config.delete()
                raise serializers.ValidationError({
                    'email_host_password': f'Failed to encrypt password: {str(e)}'
                })
                
        return config
    
    def update(self, instance, validated_data):
        password = validated_data.pop('email_host_password', None)
        
        # Update other fields first
        config = super().update(instance, validated_data)
        
        # Only update password if a new one is provided
        if password is not None and password.strip():
            try:
                config.encrypt_password(password)
                config.save()
                
                # Verify the encryption worked by testing decryption
                test_decrypt = config.decrypt_password()
                if not test_decrypt:
                    raise serializers.ValidationError({
                        'email_host_password': 'Password encryption failed. Please check your system configuration and try again.'
                    })
                elif test_decrypt != password:
                    raise serializers.ValidationError({
                        'email_host_password': 'Password encryption validation failed. Please contact system administrator.'
                    })
                    
            except Exception as e:
                raise serializers.ValidationError({
                    'email_host_password': f'Failed to encrypt password: {str(e)}'
                })
        
        return config


# Import recipient and contact group serializers
from .serializers_recipients import RecipientSerializer, ContactGroupSerializer
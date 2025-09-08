from rest_framework import serializers
from django.utils import timezone
from .models import Batch, BatchGroup, BatchRecord, BatchRecipient
from tenants.models import Group
from emails.models import EmailTemplate
from core.models_recipients import Recipient, ContactGroup
from core.models import UserEmailConfiguration


class BatchGroupSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    email_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BatchGroup
        fields = ['id', 'batch', 'group', 'group_name', 'email_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_email_count(self, obj):
        return obj.group.group_emails.filter(is_active=True).count()


class BatchRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchRecord
        fields = ['id', 'batch', 'recipient_email', 'recipient_name', 'document_received', 'marked_done', 'metadata', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BatchRecipientSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.name', read_only=True)
    recipient_email = serializers.CharField(source='recipient.email', read_only=True)
    organization = serializers.CharField(source='recipient.organization_name', read_only=True)
    reminder_number = serializers.SerializerMethodField()
    
    class Meta:
        model = BatchRecipient
        fields = ['id', 'batch', 'recipient', 'recipient_name', 'recipient_email', 
                 'organization', 'documents_received', 'email_sent', 'emails_sent_count',
                 'last_email_sent_at', 'next_email_due_at', 'is_completed', 'completed_at',
                 'reminder_number', 'created_at', 'updated_at']
        read_only_fields = ['id', 'batch', 'email_sent', 'emails_sent_count', 
                           'last_email_sent_at', 'reminder_number', 'created_at', 'updated_at']
    
    def get_reminder_number(self, obj):
        return obj.get_reminder_number()


class BatchSerializer(serializers.ModelSerializer):
    batch_groups = BatchGroupSerializer(many=True, read_only=True)
    batch_recipients = BatchRecipientSerializer(many=True, read_only=True)
    email_configuration = serializers.PrimaryKeyRelatedField(
        queryset=UserEmailConfiguration.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    template_name = serializers.CharField(source='template.name', read_only=True)
    interval_type = serializers.CharField(write_only=True, required=False)
    interval_display = serializers.CharField(source='interval_type', read_only=True)
    
    # Sub-cycle fields
    sub_cycle_interval_display = serializers.CharField(source='get_sub_cycle_interval_display', read_only=True)
    sub_cycle_custom_days = serializers.IntegerField(write_only=True, required=False, min_value=1)
    
    # Document completion count
    documents_received_count = serializers.SerializerMethodField()
    
    # For creating/updating batch with new recipient system
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of individual recipient IDs from Recipient master"
    )
    contact_group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of contact group IDs from ContactGroup master"
    )
    
    # Legacy support - will be deprecated
    group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Legacy group IDs - will be deprecated"
    )
    
    class Meta:
        model = Batch
        fields = [
            'id', 'tenant', 'template', 'template_name', 'name', 'description', 'status',
            'start_time', 'end_time', 'interval_minutes', 'interval_type', 'interval_display',
            'email_support_fields', 'total_recipients', 'emails_sent', 'emails_failed', 
            'documents_received_count', 'batch_groups', 'batch_recipients', 'group_ids', 'recipient_ids', 'contact_group_ids',
            'email_configuration',
            # Sub-cycle fields
            'sub_cycle_enabled', 'sub_cycle_interval_type', 'sub_cycle_interval_minutes', 'sub_cycle_interval_days',
            'sub_cycle_interval_display', 'sub_cycle_custom_days', 'auto_complete_on_all_received',
            'next_sub_cycle_time', 'sub_cycles_completed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'total_recipients', 'emails_sent', 'emails_failed', 
                           'sub_cycle_interval_display', 'next_sub_cycle_time', 'sub_cycles_completed', 
                           'created_at', 'updated_at']
    
    def validate_start_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Start time cannot be in the past")
        return value
    
    def validate_end_time(self, value):
        # Only validate end_time if it's provided
        if value and hasattr(self, 'initial_data'):
            start_time = self.initial_data.get('start_time')
            interval_minutes = self.initial_data.get('interval_minutes', 0)
            
            # Only validate end_time for recurring batches (interval_minutes > 0)
            if start_time and interval_minutes > 0:
                try:
                    # Parse the start time string and make it timezone-aware
                    start_dt = timezone.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    if not timezone.is_aware(start_dt):
                        start_dt = timezone.make_aware(start_dt)
                    
                    # Ensure both datetimes are timezone-aware for comparison
                    if not timezone.is_aware(value):
                        value = timezone.make_aware(value)
                    
                    if value <= start_dt:
                        raise serializers.ValidationError("End time must be after start time")
                except ValueError:
                    pass
        return value
    
    def validate_interval_minutes(self, value):
        if value < 0:
            raise serializers.ValidationError("Interval minutes cannot be negative")
        return value
    
    def validate_interval_type(self, value):
        if value not in dict(Batch.INTERVAL_CHOICES):
            raise serializers.ValidationError("Invalid interval type")
        return value
    
    def validate_group_ids(self, value):
        if not value:
            return value
        
        tenant = self.context['request'].user.tenant
        if tenant:
            from tenants.models import Group
            valid_groups = Group.objects.filter(tenant=tenant, id__in=value, is_active=True)
            if len(valid_groups) != len(value):
                raise serializers.ValidationError("One or more groups are invalid or inactive")
        
        return value
    
    def validate_recipient_ids(self, value):
        """Validate individual recipient IDs"""
        if not value:
            return value
        
        user = self.context['request'].user
        if user.role in ['super_admin', 'support_team']:
            # Super admin can access all recipients
            valid_recipients = Recipient.objects.filter(id__in=value, is_active=True)
        else:
            # Tenant users can only access their tenant's recipients
            valid_recipients = Recipient.objects.filter(
                id__in=value, 
                tenant=user.tenant, 
                is_active=True
            )
        
        if len(valid_recipients) != len(value):
            raise serializers.ValidationError("One or more recipients are invalid or inactive")
        
        return value
    
    def validate_contact_group_ids(self, value):
        """Validate contact group IDs"""
        if not value:
            return value
        
        user = self.context['request'].user
        if user.role in ['super_admin', 'support_team']:
            # Super admin can access all contact groups
            valid_groups = ContactGroup.objects.filter(id__in=value)
        else:
            # Tenant users can only access their tenant's contact groups
            valid_groups = ContactGroup.objects.filter(
                id__in=value, 
                tenant=user.tenant
            )
        
        if len(valid_groups) != len(value):
            raise serializers.ValidationError("One or more contact groups are invalid")
        
        return value
    
    def validate_template(self, value):
        user = self.context['request'].user
        tenant = user.tenant
        
        # Super admin can use any template
        if user.role == 'super_admin':
            return value
            
        # Other users can only use templates from their tenant
        if tenant and hasattr(value, 'tenant') and value.tenant != tenant:
            raise serializers.ValidationError("Template must belong to your tenant")
        return value

    def validate_email_configuration(self, value):
        if value:
            user = self.context['request'].user
            # Check if the email configuration belongs to the user
            if hasattr(value, 'user') and value.user != user:
                raise serializers.ValidationError("Email configuration must belong to you")
        return value
    
    def create(self, validated_data):
        group_ids = validated_data.pop('group_ids', [])
        recipient_ids = validated_data.pop('recipient_ids', [])
        contact_group_ids = validated_data.pop('contact_group_ids', [])
        interval_type = validated_data.pop('interval_type', None)
        sub_cycle_custom_days = validated_data.pop('sub_cycle_custom_days', None)
        
        # Set sub_cycle_interval_days if custom days provided
        if sub_cycle_custom_days:
            validated_data['sub_cycle_interval_days'] = sub_cycle_custom_days
        
        batch = super().create(validated_data)
        
        if interval_type:
            batch.set_interval_type(interval_type)
        
        # Handle sub-cycle interval setting
        if batch.sub_cycle_enabled:
            if batch.sub_cycle_interval_type == 'custom' and batch.sub_cycle_interval_days:
                # Convert days to minutes for the old method
                custom_minutes = batch.sub_cycle_interval_days * 24 * 60
                batch.set_sub_cycle_interval_minutes(
                    batch.sub_cycle_interval_type, 
                    custom_minutes
                )
            else:
                batch.set_sub_cycle_interval_minutes(
                    batch.sub_cycle_interval_type, 
                    None
                )
            # Set initial sub-cycle time
            batch.next_sub_cycle_time = batch.start_time
        
        batch.save()
        
        # Legacy group support
        if group_ids:
            for group_id in group_ids:
                BatchGroup.objects.create(batch=batch, group_id=group_id)
        
        # New recipient system
        self._add_recipients_to_batch(batch, recipient_ids, contact_group_ids)
        
        batch.total_recipients = self._calculate_total_recipients(batch)
        batch.save()
        
        return batch
    
    def update(self, instance, validated_data):
        group_ids = validated_data.pop('group_ids', None)
        recipient_ids = validated_data.pop('recipient_ids', None)
        contact_group_ids = validated_data.pop('contact_group_ids', None)
        interval_type = validated_data.pop('interval_type', None)
        
        # Validate email configuration before update
        email_config = validated_data.get('email_configuration')
        if email_config and not email_config.is_active:
            raise serializers.ValidationError({
                'email_configuration': 'The selected email configuration is not active.'
            })
        
        batch = super().update(instance, validated_data)
        
        if interval_type:
            batch.set_interval_type(interval_type)
            batch.save()
        
        # Legacy group support
        if group_ids is not None:
            BatchGroup.objects.filter(batch=batch).delete()
            for group_id in group_ids:
                BatchGroup.objects.create(batch=batch, group_id=group_id)
        
        # New recipient system
        if recipient_ids is not None or contact_group_ids is not None:
            # Clear existing batch recipients
            BatchRecipient.objects.filter(batch=batch).delete()
            # Add new recipients
            self._add_recipients_to_batch(
                batch, 
                recipient_ids or [], 
                contact_group_ids or []
            )
        
        # Recalculate total recipients if any changes were made
        if (group_ids is not None or recipient_ids is not None or 
            contact_group_ids is not None):
            batch.total_recipients = self._calculate_total_recipients(batch)
            batch.save()
        
        return batch
    
    def _add_recipients_to_batch(self, batch, recipient_ids, contact_group_ids):
        """Add recipients to batch from individual recipients and contact groups"""
        recipients_to_add = set()
        
        # Add individual recipients
        if recipient_ids:
            individual_recipients = Recipient.objects.filter(
                id__in=recipient_ids,
                is_active=True
            )
            recipients_to_add.update(individual_recipients)
        
        # Add recipients from contact groups
        if contact_group_ids:
            group_recipients = Recipient.objects.filter(
                groups__id__in=contact_group_ids,
                is_active=True
            ).distinct()
            recipients_to_add.update(group_recipients)
        
        # Create BatchRecipient objects
        batch_recipients = []
        for recipient in recipients_to_add:
            batch_recipients.append(
                BatchRecipient(
                    batch=batch, 
                    recipient=recipient,
                    next_email_due_at=batch.start_time  # Set to batch start time so they're ready immediately
                )
            )
        
        if batch_recipients:
            BatchRecipient.objects.bulk_create(batch_recipients, ignore_conflicts=True)
    
    def get_documents_received_count(self, obj):
        """Get count of recipients who have submitted documents"""
        # Count from new BatchRecipient system
        new_system_count = obj.batch_recipients.filter(is_completed=True).count()
        
        # Count from legacy BatchRecord system
        try:
            from .models import BatchRecord
            legacy_system_count = BatchRecord.objects.filter(
                batch=obj,
                document_received=True
            ).count()
        except:
            legacy_system_count = 0
        
        return new_system_count + legacy_system_count
    
    def _calculate_total_recipients(self, batch):
        """Calculate total recipients from both legacy groups and new recipient system"""
        total = 0
        
        # Count from legacy groups (Group -> GroupEmail)
        for batch_group in batch.batch_groups.all():
            total += batch_group.group.group_emails.filter(is_active=True).count()
        
        # Count from new recipient system (BatchRecipient)
        total += batch.batch_recipients.count()
        
        return total


class BatchCreateSerializer(serializers.ModelSerializer):
    # Legacy support
    group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )
    
    # New recipient system
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of individual recipient IDs from Recipient master"
    )
    contact_group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of contact group IDs from ContactGroup master"
    )
    
    email_configuration = serializers.PrimaryKeyRelatedField(
        queryset=UserEmailConfiguration.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        help_text="ID of the email configuration to use for this batch. If not provided, default configuration will be used."
    )
    
    interval_type = serializers.CharField(write_only=True, required=False)
    sub_cycle_custom_days = serializers.IntegerField(write_only=True, required=False, min_value=1)
    
    def validate(self, data):
        """Ensure at least one recipient source is provided and validate sub-cycle settings"""
        group_ids = data.get('group_ids', [])
        recipient_ids = data.get('recipient_ids', [])
        contact_group_ids = data.get('contact_group_ids', [])
        
        if not (group_ids or recipient_ids or contact_group_ids):
            raise serializers.ValidationError(
                "At least one of group_ids, recipient_ids, or contact_group_ids must be provided"
            )
        
        # Validate sub-cycle settings only if enabled
        sub_cycle_enabled = data.get('sub_cycle_enabled', False)
        if sub_cycle_enabled:
            sub_cycle_interval_type = data.get('sub_cycle_interval_type', 'daily')
            sub_cycle_custom_days = data.get('sub_cycle_custom_days')
            
            if sub_cycle_interval_type == 'custom' and not sub_cycle_custom_days:
                raise serializers.ValidationError({
                    'sub_cycle_custom_days': 'Custom days is required when sub-cycle interval type is custom'
                })
            elif sub_cycle_interval_type == 'custom' and sub_cycle_custom_days < 1:
                raise serializers.ValidationError({
                    'sub_cycle_custom_days': 'Custom days must be at least 1 day'
                })
        
        # Validate end_time only for recurring batches
        interval_minutes = data.get('interval_minutes', 0)
        end_time = data.get('end_time')
        
        # Only require end_time for recurring batches (interval_minutes > 0)
        if interval_minutes > 0 and not end_time:
            raise serializers.ValidationError({
                'end_time': 'End time is required for recurring batches'
            })
        
        # For one-time batches (interval_minutes = 0), end_time should be None or not provided
        if interval_minutes == 0 and end_time:
            # Remove end_time for one-time batches to avoid validation issues
            data['end_time'] = None
        
        return data
    
    class Meta:
        model = Batch
        fields = [
            'template', 'name', 'description', 'start_time', 'end_time',
            'interval_minutes', 'interval_type', 'email_support_fields', 
            'group_ids', 'recipient_ids', 'contact_group_ids', 'email_configuration',
            'sub_cycle_enabled', 'sub_cycle_interval_type', 'sub_cycle_interval_days',
            'sub_cycle_custom_days', 'auto_complete_on_all_received'
        ]
    
    def validate_start_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Start time cannot be in the past")
        return value
    
    def validate_end_time(self, value):
        # Only validate end_time if it's provided
        if value and hasattr(self, 'initial_data'):
            start_time = self.initial_data.get('start_time')
            interval_minutes = self.initial_data.get('interval_minutes', 0)
            
            # Only validate end_time for recurring batches (interval_minutes > 0)
            if start_time and interval_minutes > 0:
                try:
                    # Parse the start time string and make it timezone-aware
                    start_dt = timezone.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    if not timezone.is_aware(start_dt):
                        start_dt = timezone.make_aware(start_dt)
                    
                    # Ensure both datetimes are timezone-aware for comparison
                    if not timezone.is_aware(value):
                        value = timezone.make_aware(value)
                    
                    if value <= start_dt:
                        raise serializers.ValidationError("End time must be after start time")
                except ValueError:
                    pass
        return value
    
    def validate_group_ids(self, value):
        if not value:
            return value
            
        tenant = self.context['request'].user.tenant
        if tenant:
            valid_groups = Group.objects.filter(tenant=tenant, id__in=value, is_active=True)
            if len(valid_groups) != len(value):
                raise serializers.ValidationError("One or more groups are invalid or inactive")
        
        return value
    
    def validate_recipient_ids(self, value):
        """Validate individual recipient IDs"""
        if not value:
            return value
        
        user = self.context['request'].user
        if user.role in ['super_admin', 'support_team']:
            # Super admin can access all recipients
            valid_recipients = Recipient.objects.filter(id__in=value, is_active=True)
        else:
            # Tenant users can only access their tenant's recipients
            valid_recipients = Recipient.objects.filter(
                id__in=value, 
                tenant=user.tenant, 
                is_active=True
            )
        
        if len(valid_recipients) != len(value):
            raise serializers.ValidationError("One or more recipients are invalid or inactive")
        
        return value
    
    def validate_contact_group_ids(self, value):
        """Validate contact group IDs"""
        if not value:
            return value
        
        user = self.context['request'].user
        if user.role in ['super_admin', 'support_team']:
            # Super admin can access all contact groups
            valid_groups = ContactGroup.objects.filter(id__in=value)
        else:
            # Tenant users can only access their tenant's contact groups
            valid_groups = ContactGroup.objects.filter(
                id__in=value, 
                tenant=user.tenant
            )
        
        if len(valid_groups) != len(value):
            raise serializers.ValidationError("One or more contact groups are invalid")
        
        return value
    
    def validate_template(self, value):
        user = self.context['request'].user
        tenant = user.tenant
        
        # Super admin can use any template
        if user.role == 'super_admin':
            return value
            
        # Other users can only use templates from their tenant
        if tenant and hasattr(value, 'tenant') and value.tenant != tenant:
            raise serializers.ValidationError("Template must belong to your tenant")
        return value

    def validate_email_configuration(self, value):
        if value:
            user = self.context['request'].user
            # Check if the email configuration belongs to the user
            if hasattr(value, 'user') and value.user != user:
                raise serializers.ValidationError("Email configuration must belong to you")
        return value
    
    def create(self, validated_data):
        group_ids = validated_data.pop('group_ids', [])
        recipient_ids = validated_data.pop('recipient_ids', [])
        contact_group_ids = validated_data.pop('contact_group_ids', [])
        interval_type = validated_data.pop('interval_type', None)
        sub_cycle_custom_days = validated_data.pop('sub_cycle_custom_days', None)
        
        # Set sub_cycle_interval_days if custom days provided
        if sub_cycle_custom_days:
            validated_data['sub_cycle_interval_days'] = sub_cycle_custom_days
        
        # Set the tenant for the batch
        user = self.context['request'].user
        if user.role != 'super_admin':
            validated_data['tenant'] = user.tenant
        
        # Handle email configuration
        email_config = validated_data.get('email_configuration')
        if not email_config:
            # If no specific configuration provided, try to find the default one
            if user.tenant:
                # First try to find user's default configuration
                email_config = UserEmailConfiguration.objects.filter(
                    user=user,
                    is_active=True,
                    is_default=True
                ).first()
                
                # If no user default, try to find tenant's default configuration
                if not email_config:
                    email_config = UserEmailConfiguration.objects.filter(
                        user__tenant=user.tenant,
                        is_active=True,
                        is_default=True
                    ).first()
                
                if email_config:
                    validated_data['email_configuration'] = email_config
                else:
                    # Look for any active configuration for the user
                    email_config = UserEmailConfiguration.objects.filter(
                        user=user,
                        is_active=True
                    ).first()
                    
                    if email_config:
                        validated_data['email_configuration'] = email_config
                    else:
                        raise serializers.ValidationError({
                            'email_configuration': 'No active email configuration found. Please set up email configuration in your profile settings first.'
                        })
        
        batch = super().create(validated_data)
        
        if interval_type:
            batch.set_interval_type(interval_type)
        
        # Handle sub-cycle interval setting
        if batch.sub_cycle_enabled:
            if batch.sub_cycle_interval_type == 'custom' and batch.sub_cycle_interval_days:
                # Convert days to minutes for the old method
                custom_minutes = batch.sub_cycle_interval_days * 24 * 60
                batch.set_sub_cycle_interval_minutes(
                    batch.sub_cycle_interval_type, 
                    custom_minutes
                )
            else:
                batch.set_sub_cycle_interval_minutes(
                    batch.sub_cycle_interval_type, 
                    None
                )
            # Set initial sub-cycle time
            batch.next_sub_cycle_time = batch.start_time
        
        batch.save()
        
        # Legacy group support
        if group_ids:
            for group_id in group_ids:
                BatchGroup.objects.create(batch=batch, group_id=group_id)
        
        # New recipient system
        self._add_recipients_to_batch(batch, recipient_ids, contact_group_ids)
        
        # Calculate total recipients
        batch.total_recipients = self._calculate_total_recipients(batch)
        batch.save()
        
        return batch
    
    def _add_recipients_to_batch(self, batch, recipient_ids, contact_group_ids):
        """Add recipients to batch from individual recipients and contact groups"""
        recipients_to_add = set()
        
        # Add individual recipients
        if recipient_ids:
            individual_recipients = Recipient.objects.filter(
                id__in=recipient_ids,
                is_active=True
            )
            recipients_to_add.update(individual_recipients)
        
        # Add recipients from contact groups
        if contact_group_ids:
            group_recipients = Recipient.objects.filter(
                groups__id__in=contact_group_ids,
                is_active=True
            ).distinct()
            recipients_to_add.update(group_recipients)
        
        # Create BatchRecipient objects
        batch_recipients = []
        for recipient in recipients_to_add:
            batch_recipients.append(
                BatchRecipient(batch=batch, recipient=recipient)
            )
        
        if batch_recipients:
            BatchRecipient.objects.bulk_create(batch_recipients, ignore_conflicts=True)
    
    def _calculate_total_recipients(self, batch):
        """Calculate total recipients from both legacy groups and new recipient system"""
        total = 0
        
        # Count from legacy groups (Group -> GroupEmail)
        for batch_group in batch.batch_groups.all():
            total += batch_group.group.group_emails.filter(is_active=True).count()
        
        # Count from new recipient system (BatchRecipient)
        total += batch.batch_recipients.count()
        
        return total


class BatchActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['start', 'pause', 'resume', 'cancel'])
    
    def validate(self, data):
        batch = self.context.get('batch')
        if not batch:
            raise serializers.ValidationError("Batch not found")
        
        action = data['action']
        
        # Validate batch status transitions
        valid_transitions = {
            'draft': ['start'],
            'scheduled': ['cancel', 'pause'],
            'running': ['pause', 'cancel'],
            'paused': ['resume', 'cancel'],
            'completed': [],
            'cancelled': [],
            'failed': ['start']
        }
        
        if action not in valid_transitions.get(batch.status, []):
            raise serializers.ValidationError(f"Cannot {action} batch in {batch.status} status")
        
        # Additional validations for start/resume actions
        if action in ['start', 'resume']:
            # Check email configuration
            if not batch.email_configuration:
                raise serializers.ValidationError(
                    "No email configuration found. Please configure email settings first."
                )
            
            if not batch.email_configuration.is_active:
                raise serializers.ValidationError(
                    "Email configuration is not active. Please update email settings."
                )
            
            # Check recipients
            if batch.total_recipients == 0:
                raise serializers.ValidationError(
                    "No recipients found. Please add recipients before starting the batch."
                )
            
            # Validate template
            if not batch.template:
                raise serializers.ValidationError(
                    "No email template assigned to this batch."
                )
        
        return data


# =============================================================================
# 🚀 ENHANCED SERIALIZER FUNCTIONALITY - MERGED FROM enhanced_serializers.py
# =============================================================================

class EnhancedBatchSerializer(serializers.ModelSerializer):
    """Enhanced batch serializer with AI analytics and performance metrics"""
    
    # Basic fields
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_subject = serializers.CharField(source='template.subject', read_only=True)
    email_config_name = serializers.CharField(source='email_configuration.from_email', read_only=True)
    
    # Calculated fields
    success_rate = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    performance_grade = serializers.SerializerMethodField()
    estimated_duration = serializers.SerializerMethodField()
    
    # Status information
    can_pause = serializers.SerializerMethodField()
    can_resume = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_duplicate = serializers.SerializerMethodField()
    
    # Recipient counts
    total_legacy_recipients = serializers.SerializerMethodField()
    total_new_recipients = serializers.SerializerMethodField()
    active_recipients = serializers.SerializerMethodField()
    
    class Meta:
        model = Batch
        fields = [
            'id', 'name', 'description', 'status', 'created_at', 'updated_at',
            'start_time', 'end_time', 'interval_minutes', 'total_recipients',
            'emails_sent', 'emails_failed', 'template_name', 'template_subject',
            'email_config_name', 'success_rate', 'completion_rate', 'performance_grade',
            'estimated_duration', 'can_pause', 'can_resume',
            'can_cancel', 'can_duplicate', 'total_legacy_recipients',
            'total_new_recipients', 'active_recipients', 'sub_cycle_enabled',
            'sub_cycle_interval', 'sub_cycle_count', 'sub_cycles_completed'
        ]
    
    def get_success_rate(self, obj):
        """Calculate success rate percentage"""
        total_processed = (obj.emails_sent or 0) + (obj.emails_failed or 0)
        if total_processed == 0:
            return 0
        return round((obj.emails_sent or 0) / total_processed * 100, 2)
    
    def get_completion_rate(self, obj):
        """Calculate completion rate percentage"""
        if not obj.total_recipients:
            return 0
        total_processed = (obj.emails_sent or 0) + (obj.emails_failed or 0)
        return round(total_processed / obj.total_recipients * 100, 2)
    
    def get_performance_grade(self, obj):
        """Calculate performance grade based on success and engagement rates"""
        success_rate = self.get_success_rate(obj)
        
        if success_rate >= 90:
            return 'Excellent'
        elif success_rate >= 80:
            return 'Very Good'
        elif success_rate >= 70:
            return 'Good'
        elif success_rate >= 60:
            return 'Average'
        else:
            return 'Needs Improvement'
    
    def get_estimated_duration(self, obj):
        """Estimate batch completion duration in minutes"""
        if obj.status == 'completed':
            return 0
        
        total_recipients = obj.total_recipients or 0
        if total_recipients == 0:
            return 0
        
        # Estimate based on sending rate (assume 60 emails per minute)
        estimated_minutes = total_recipients / 60
        
        # Add buffer for processing and intervals
        if obj.interval_minutes > 0:
            estimated_minutes += obj.interval_minutes * 0.1
        
        return round(estimated_minutes, 1)
    
    def get_can_pause(self, obj):
        """Check if batch can be paused"""
        return obj.status == 'running'
    
    def get_can_resume(self, obj):
        """Check if batch can be resumed"""
        return obj.status == 'paused'
    
    def get_can_cancel(self, obj):
        """Check if batch can be cancelled"""
        return obj.status in ['draft', 'scheduled', 'running', 'paused']
    
    def get_can_duplicate(self, obj):
        """Check if batch can be duplicated"""
        return obj.status in ['completed', 'cancelled', 'failed']
    
    def get_total_legacy_recipients(self, obj):
        """Count recipients from legacy group system"""
        total = 0
        for batch_group in obj.batch_groups.all():
            total += batch_group.group.group_emails.filter(is_active=True).count()
        return total
    
    def get_total_new_recipients(self, obj):
        """Count recipients from new recipient system"""
        return obj.batch_recipients.count()
    
    def get_active_recipients(self, obj):
        """Count active recipients (not bounced/unsubscribed)"""
        # This could be enhanced to check recipient status
        return obj.total_recipients or 0


class BatchDuplicationSerializer(serializers.Serializer):
    """Serializer for batch duplication requests"""
    
    name = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Name for the duplicated batch"
    )
    copy_recipients = serializers.BooleanField(
        default=True,
        help_text="Whether to copy recipients to the new batch"
    )
    copy_schedule = serializers.BooleanField(
        default=False,
        help_text="Whether to copy the schedule to the new batch"
    )
    auto_optimize = serializers.BooleanField(
        default=True,
        help_text="Whether to generate AI optimization suggestions"
    )
    
    def validate_name(self, value):
        """Validate duplicate batch name"""
        if value:
            user = self.context['request'].user
            tenant = user.tenant
            
            # Check if name already exists for this tenant
            existing_batch = Batch.objects.filter(
                tenant=tenant,
                name=value
            ).exists()
            
            if existing_batch:
                raise serializers.ValidationError(
                    "A batch with this name already exists"
                )
        
        return value


class BatchAnalyticsSerializer(serializers.Serializer):
    """Serializer for batch analytics responses"""
    
    batch_info = serializers.DictField()
    metrics = serializers.DictField()
    performance = serializers.DictField()
    timeline = serializers.ListField()
    recommendations = serializers.ListField()
    
    class Meta:
        fields = [
            'batch_info', 'metrics', 'performance', 
            'timeline', 'recommendations'
        ]
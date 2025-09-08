from rest_framework import serializers
from .models_recipients import ContactGroup, Recipient

class ContactGroupSerializer(serializers.ModelSerializer):
    recipient_count = serializers.SerializerMethodField()

    class Meta:
        model = ContactGroup
        fields = ['id', 'name', 'description', 'recipient_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_recipient_count(self, obj):
        return obj.recipients.count()

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['tenant'] = request.user.tenant
        validated_data['created_by'] = request.user
        return super().create(validated_data)

class RecipientSerializer(serializers.ModelSerializer):
    groups = ContactGroupSerializer(many=True, read_only=True)
    group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Recipient
        fields = ['id', 'name', 'organization_name', 'email', 'groups', 'group_ids',
                 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['created_at', 'updated_at']

    def validate_group_ids(self, value):
        request = self.context.get('request')
        if value:
            groups = ContactGroup.objects.filter(
                id__in=value,
                tenant=request.user.tenant
            )
            if len(groups) != len(value):
                raise serializers.ValidationError("One or more invalid group IDs")
        return value

    def create(self, validated_data):
        group_ids = validated_data.pop('group_ids', [])
        request = self.context.get('request')
        validated_data['tenant'] = request.user.tenant
        validated_data['created_by'] = request.user
        
        recipient = super().create(validated_data)
        
        if group_ids:
            groups = ContactGroup.objects.filter(
                id__in=group_ids,
                tenant=request.user.tenant
            )
            recipient.groups.set(groups)
        
        return recipient

    def update(self, instance, validated_data):
        group_ids = validated_data.pop('group_ids', None)
        instance = super().update(instance, validated_data)
        
        if group_ids is not None:
            groups = ContactGroup.objects.filter(
                id__in=group_ids,
                tenant=instance.tenant
            )
            instance.groups.set(groups)
        
        return instance

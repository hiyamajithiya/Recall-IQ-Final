from django.contrib import admin
from .models import Tenant, TenantEmail, TenantMailSecret, Group, GroupEmail


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']


@admin.register(TenantEmail)
class TenantEmailAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'email', 'display_name', 'is_active', 'created_at']
    list_filter = ['tenant', 'is_active', 'created_at']
    search_fields = ['email', 'display_name']


@admin.register(TenantMailSecret)
class TenantMailSecretAdmin(admin.ModelAdmin):
    list_display = ['tenant_email', 'provider', 'is_active', 'created_at']
    list_filter = ['provider', 'is_active', 'created_at']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'name', 'is_active', 'created_at']
    list_filter = ['tenant', 'is_active', 'created_at']
    search_fields = ['name', 'description']


@admin.register(GroupEmail)
class GroupEmailAdmin(admin.ModelAdmin):
    list_display = ['group', 'email', 'name', 'is_active', 'created_at']
    list_filter = ['group__tenant', 'is_active', 'created_at']
    search_fields = ['email', 'name']
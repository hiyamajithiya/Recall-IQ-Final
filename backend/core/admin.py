from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'tenant')}),
    )
    list_display = ['username', 'email', 'role', 'tenant', 'is_active']
    list_filter = ['role', 'tenant', 'is_active']
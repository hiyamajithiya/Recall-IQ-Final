from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'super_admin'


class IsSuperAdminOrSupportTeam(permissions.BasePermission):
    """
    Permission class that allows both super_admin and support_team roles
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['super_admin', 'support_team'])


class IsSuperAdminOrSupportTeamNonDestructive(permissions.BasePermission):
    """
    Permission class that allows super_admin and support_team, but blocks deletion operations for support_team
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Super admin has all permissions
        if request.user.role == 'super_admin':
            return True
        
        # Support team has all permissions except DELETE operations
        if request.user.role == 'support_team':
            # Block DELETE method and destroy action
            if request.method == 'DELETE':
                return False
            if hasattr(view, 'action') and view.action == 'destroy':
                return False
            return True
        
        return False


class IsTenantAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['super_admin', 'support_team', 'tenant_admin', 'staff_admin', 'sales_team'])


class IsTenantMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['super_admin', 'support_team', 'tenant_admin', 'staff_admin', 'staff', 'sales_team'])


class IsTenantStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.role in ['super_admin', 'support_team', 'tenant_admin', 'staff_admin', 'staff', 'sales_team'])


class IsTenantOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Support team has same global access as super_admin
        if request.user.role in ['super_admin', 'support_team']:
            return True
        
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        
        if hasattr(obj, 'tenant_id'):
            return obj.tenant_id == request.user.tenant.id if request.user.tenant else False
        
        return False


class IsOwnerOrTenantAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Support team has same global access as super_admin
        if request.user.role in ['super_admin', 'support_team']:
            return True
        
        if request.user.role in ['tenant_admin', 'staff_admin', 'sales_team']:
            if hasattr(obj, 'tenant'):
                return obj.tenant == request.user.tenant
            if hasattr(obj, 'tenant_id'):
                return obj.tenant_id == request.user.tenant.id if request.user.tenant else False
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsTenantUser(permissions.BasePermission):
    """
    Permission class to check if user belongs to a tenant and has one of the allowed roles
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                request.user.tenant and 
                request.user.role in ['tenant_admin', 'staff_admin', 'staff', 'sales_team'])

    def has_object_permission(self, request, view, obj):
        if not request.user.tenant:
            return False
            
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
            
        if hasattr(obj, 'tenant_id'):
            return obj.tenant_id == request.user.tenant.id
            
        return False
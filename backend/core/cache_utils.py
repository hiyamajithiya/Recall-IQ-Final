"""
Cache utilities for dashboard performance optimization
"""
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def invalidate_dashboard_cache(tenant_id=None):
    """Invalidate dashboard cache for specific tenant or all tenants"""
    if tenant_id:
        cache_key = f'tenant_dashboard_{tenant_id}'
        cache.delete(cache_key)
        logger.debug(f"Invalidated dashboard cache for tenant {tenant_id}")
    else:
        # Invalidate super admin dashboard cache
        cache.delete('super_admin_dashboard')
        logger.debug("Invalidated super admin dashboard cache")


def invalidate_tenant_cache(tenant_id):
    """Invalidate all caches related to a specific tenant"""
    cache_keys = [
        f'tenant_dashboard_{tenant_id}',
        'super_admin_dashboard',  # Super admin dashboard shows data from all tenants
    ]
    
    cache.delete_many(cache_keys)
    logger.debug(f"Invalidated all cache keys for tenant {tenant_id}")


def get_cache_key(cache_type, identifier=None):
    """Generate standardized cache keys"""
    if cache_type == 'super_admin_dashboard':
        return 'super_admin_dashboard'
    elif cache_type == 'tenant_dashboard' and identifier:
        return f'tenant_dashboard_{identifier}'
    else:
        raise ValueError(f"Invalid cache type: {cache_type}")


def warm_dashboard_cache(tenant_id=None):
    """Pre-warm dashboard cache (can be called from management commands)"""
    if tenant_id:
        from tenants.models import Tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            from core.dashboard_views import _get_tenant_dashboard
            _get_tenant_dashboard(tenant)
            logger.info(f"Warmed dashboard cache for tenant {tenant_id}")
        except Tenant.DoesNotExist:
            logger.error(f"Tenant {tenant_id} not found for cache warming")
    else:
        from core.dashboard_views import _get_super_admin_dashboard
        _get_super_admin_dashboard()
        logger.info("Warmed super admin dashboard cache")
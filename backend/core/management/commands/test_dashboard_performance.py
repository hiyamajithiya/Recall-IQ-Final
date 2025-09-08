"""
Management command to test dashboard performance

This command tests the performance improvements made to dashboard views
and provides detailed metrics on query optimization.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from tenants.models import Tenant
from core.dashboard_views import _get_tenant_dashboard, _get_super_admin_dashboard
import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Test dashboard performance improvements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=3,
            help='Number of test iterations',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear cache before testing',
        )

    def handle(self, *args, **options):
        iterations = options.get('iterations', 3)
        
        if options.get('clear_cache'):
            cache.clear()
            self.stdout.write('Cache cleared')
        
        self.stdout.write(self.style.SUCCESS('Starting dashboard performance tests...'))
        
        # Get test data
        tenant = Tenant.objects.first()
        admin = User.objects.filter(role='super_admin').first()
        
        if not tenant:
            self.stdout.write(self.style.ERROR('No tenant found for testing'))
            return
        
        if not admin:
            self.stdout.write(self.style.ERROR('No admin user found for testing'))
            return
        
        self.test_tenant_dashboard_performance(tenant, iterations)
        self.test_super_admin_dashboard_performance(iterations)
        self.test_database_query_count(tenant)
        
        self.stdout.write(self.style.SUCCESS('Dashboard performance tests completed!'))

    def test_tenant_dashboard_performance(self, tenant, iterations):
        """Test tenant dashboard performance"""
        self.stdout.write(f'\n=== Tenant Dashboard Performance Test ({iterations} iterations) ===')
        
        cache_key = f'tenant_dashboard_{tenant.id}'
        
        # Test without cache (fresh data)
        cache.delete(cache_key)
        times_no_cache = []
        
        for i in range(iterations):
            cache.delete(cache_key)  # Ensure no cache
            start_time = time.time()
            result = _get_tenant_dashboard(tenant)
            end_time = time.time()
            times_no_cache.append(end_time - start_time)
        
        avg_no_cache = sum(times_no_cache) / len(times_no_cache)
        
        # Test with cache
        times_with_cache = []
        
        for i in range(iterations):
            start_time = time.time()
            result = _get_tenant_dashboard(tenant)  # Should use cache after first call
            end_time = time.time()
            times_with_cache.append(end_time - start_time)
        
        avg_with_cache = sum(times_with_cache) / len(times_with_cache)
        
        improvement = avg_no_cache / avg_with_cache if avg_with_cache > 0 else 0
        
        self.stdout.write(f'Average time without cache: {avg_no_cache:.4f} seconds')
        self.stdout.write(f'Average time with cache: {avg_with_cache:.4f} seconds')
        self.stdout.write(f'Performance improvement: {improvement:.1f}x faster')
        
        # Test data structure
        self.stdout.write(f'Dashboard sections: {len(result)} main sections')
        self.stdout.write(f'Overview metrics: {len(result["overview"])} metrics')

    def test_super_admin_dashboard_performance(self, iterations):
        """Test super admin dashboard performance"""
        self.stdout.write(f'\n=== Super Admin Dashboard Performance Test ({iterations} iterations) ===')
        
        cache_key = 'super_admin_dashboard'
        
        # Test without cache
        cache.delete(cache_key)
        times_no_cache = []
        
        for i in range(iterations):
            cache.delete(cache_key)
            start_time = time.time()
            result = _get_super_admin_dashboard()
            end_time = time.time()
            times_no_cache.append(end_time - start_time)
        
        avg_no_cache = sum(times_no_cache) / len(times_no_cache)
        
        # Test with cache
        times_with_cache = []
        
        for i in range(iterations):
            start_time = time.time()
            result = _get_super_admin_dashboard()
            end_time = time.time()
            times_with_cache.append(end_time - start_time)
        
        avg_with_cache = sum(times_with_cache) / len(times_with_cache)
        
        improvement = avg_no_cache / avg_with_cache if avg_with_cache > 0 else 0
        
        self.stdout.write(f'Average time without cache: {avg_no_cache:.4f} seconds')
        self.stdout.write(f'Average time with cache: {avg_with_cache:.4f} seconds')
        self.stdout.write(f'Performance improvement: {improvement:.1f}x faster')

    def test_database_query_count(self, tenant):
        """Test database query count optimization"""
        self.stdout.write(f'\n=== Database Query Count Test ===')
        
        # Clear cache to force database queries
        cache.clear()
        
        # Count queries for tenant dashboard
        connection.queries_log.clear()
        result = _get_tenant_dashboard(tenant)
        tenant_queries = len(connection.queries_log)
        
        # Count queries for super admin dashboard
        connection.queries_log.clear()
        result = _get_super_admin_dashboard()
        admin_queries = len(connection.queries_log)
        
        self.stdout.write(f'Tenant dashboard queries: {tenant_queries}')
        self.stdout.write(f'Super admin dashboard queries: {admin_queries}')
        
        if tenant_queries <= 10:
            self.stdout.write(self.style.SUCCESS('✓ Tenant dashboard queries are optimized'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Tenant dashboard uses {tenant_queries} queries (target: ≤10)'))
        
        if admin_queries <= 8:
            self.stdout.write(self.style.SUCCESS('✓ Super admin dashboard queries are optimized'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Super admin dashboard uses {admin_queries} queries (target: ≤8)'))

    def show_query_details(self):
        """Show detailed query information for debugging"""
        self.stdout.write(f'\n=== Query Details ===')
        for i, query in enumerate(connection.queries_log, 1):
            self.stdout.write(f'{i}. {query["sql"][:100]}... ({query["time"]}s)')
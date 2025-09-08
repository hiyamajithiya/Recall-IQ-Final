"""
RecallIQ - Dashboard views for analytics and insights
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q, Sum, Avg, F, Prefetch
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from tenants.models import Tenant, TenantEmail, Group, GroupEmail
from emails.models import EmailTemplate
from batches.models import Batch
from logs.models import EmailLog
from core.permissions import IsTenantMember
from core.models import User
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tenant_dashboard(request):
    user = request.user
    
    # Safe access to tenant
    tenant = None
    if hasattr(user, 'tenant') and user.tenant:
        tenant = user.tenant
    
    if user.role in ['super_admin', 'support_team']:
        dashboard_data = _get_super_admin_dashboard()
    elif tenant:
        dashboard_data = _get_tenant_dashboard(tenant)
    else:
        dashboard_data = _get_empty_dashboard()
    
    dashboard_data['user'] = {
        'username': user.username,
        'role': user.role,
        'tenant': tenant.name if tenant else None,
        'tenant_id': tenant.id if tenant else None,
        'first_name': user.first_name,
    }
    
    return Response(dashboard_data)


def _get_super_admin_dashboard():
    # Cache key for super admin dashboard
    cache_key = 'super_admin_dashboard'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.debug("Returning cached super admin dashboard data")
        return cached_data
    
    logger.debug("Generating fresh super admin dashboard data")
    
    # Use aggregate to get counts in a single query
    tenant_stats = Tenant.objects.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status='active')),
        trial=Count('id', filter=Q(status='trial'))
    )
    
    user_count = User.objects.count()
    
    # Get email stats in single query
    email_stats = EmailLog.objects.aggregate(
        sent=Count('id', filter=Q(status='sent')),
        failed=Count('id', filter=Q(status='failed'))
    )
    
    # Calculate revenue efficiently using aggregation
    plan_pricing = {
        'starter': 29,
        'professional': 99,
        'enterprise': 299,
        'custom': 499
    }
    
    # Use case/when to calculate revenue in database
    from django.db.models import Case, When, IntegerField
    revenue_annotation = Case(
        When(plan='starter', then=29),
        When(plan='professional', then=99),
        When(plan='enterprise', then=299),
        When(plan='custom', then=499),
        default=29,
        output_field=IntegerField()
    )
    
    monthly_revenue = Tenant.objects.filter(status='active').aggregate(
        total=Sum(revenue_annotation)
    )['total'] or 0
    
    # Get recent tenants with minimal data
    recent_tenants = Tenant.objects.filter(
        is_active=True
    ).only(
        'id', 'name', 'contact_email', 'plan', 'status', 'created_at'
    ).order_by('-created_at')[:5]
    
    total_emails = email_stats['sent'] + email_stats['failed']
    success_rate = (email_stats['sent'] / total_emails * 100) if total_emails > 0 else 0
    
    dashboard_data = {
        'overview': {
            'total_tenants': tenant_stats['total'],
            'active_tenants': tenant_stats['active'],
            'trial_tenants': tenant_stats['trial'],
            'total_users': user_count,
            'monthly_revenue': monthly_revenue,
            'total_emails_sent': email_stats['sent'],
            'total_emails_failed': email_stats['failed'],
            'success_rate': round(success_rate, 2)
        },
        'recent_tenants': [
            {
                'id': tenant.id,
                'name': tenant.name,
                'contact_email': tenant.contact_email,
                'plan': tenant.plan,
                'status': tenant.status,
                'created_at': tenant.created_at
            } for tenant in recent_tenants
        ],
        'system_health': _get_system_health()
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, dashboard_data, 300)
    return dashboard_data


def _get_tenant_dashboard(tenant):
    # Cache key specific to this tenant
    cache_key = f'tenant_dashboard_{tenant.id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.debug(f"Returning cached dashboard data for tenant {tenant.id}")
        return cached_data
    
    logger.debug(f"Generating fresh dashboard data for tenant {tenant.id}")
    
    # Optimize counts with single queries
    overview_stats = {
        'total_groups': Group.objects.filter(tenant=tenant, is_active=True).count(),
        'total_contacts': GroupEmail.objects.filter(group__tenant=tenant, is_active=True).count(),
        'total_templates': EmailTemplate.objects.filter(tenant=tenant, is_active=True).count()
    }
    
    # Batch statistics in single query using aggregation
    batch_stats = Batch.objects.filter(tenant=tenant).aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status__in=['scheduled', 'running'])),
        completed=Count('id', filter=Q(status='completed'))
    )
    
    # Email statistics in single query
    email_stats = EmailLog.objects.filter(tenant=tenant).aggregate(
        sent_outgoing=Count('id', filter=Q(status='sent', direction='outgoing')),
        sent_incoming=Count('id', filter=Q(status='sent', direction='incoming')),
        failed=Count('id', filter=Q(status='failed')),
        pending=Count('id', filter=Q(status='queued'))
    )
    
    emails_sent = email_stats['sent_outgoing']
    total_emails_failed = email_stats['failed']
    success_rate = (emails_sent / (emails_sent + total_emails_failed) * 100) if (emails_sent + total_emails_failed) > 0 else 0
    
    # Optimize related queries with select_related and only() 
    recent_batches = Batch.objects.filter(
        tenant=tenant
    ).select_related('template').only(
        'id', 'name', 'status', 'total_recipients', 'emails_sent', 'created_at',
        'template__name'
    ).order_by('-created_at')[:5]
    
    recent_emails = EmailLog.objects.filter(
        tenant=tenant
    ).only(
        'id', 'email_type', 'status', 'direction', 'to_email', 'subject', 'created_at'
    ).order_by('-created_at')[:10]
    
    # Optimize time-based queries
    now = timezone.now()
    last_7_days = now - timedelta(days=7)
    next_7_days = now + timedelta(days=7)
    
    upcoming_batches = Batch.objects.filter(
        tenant=tenant,
        status='scheduled',
        start_time__gte=now,
        start_time__lte=next_7_days
    ).select_related('template').only(
        'id', 'name', 'start_time', 'total_recipients', 'template__name'
    ).order_by('start_time')[:5]
    
    # Get email activity chart and performance metrics
    email_activity = _get_email_activity_chart_optimized(tenant, last_7_days)
    performance_metrics = _get_performance_metrics_optimized(tenant)
    
    dashboard_data = {
        'overview': {
            'total_groups': overview_stats['total_groups'],
            'total_contacts': overview_stats['total_contacts'],
            'total_templates': overview_stats['total_templates'],
            'total_batches': batch_stats['total'],
            'active_batches': batch_stats['active'],
            'completed_batches': batch_stats['completed'],
            'total_emails_sent': emails_sent,
            'emails_sent': emails_sent,
            'emails_received': email_stats['sent_incoming'],
            'total_emails_failed': total_emails_failed,
            'pending_emails': email_stats['pending'],
            'success_rate': round(success_rate, 2)
        },
        'recent_batches': [
            {
                'id': batch.id,
                'name': batch.name,
                'template_name': batch.template.name if batch.template else 'No Template',
                'status': batch.status,
                'total_recipients': batch.total_recipients,
                'emails_sent': batch.emails_sent,
                'created_at': batch.created_at
            } for batch in recent_batches
        ],
        'recent_email_activity': [
            {
                'id': email.id,
                'email_type': email.email_type,
                'status': email.status,
                'direction': email.direction,
                'to_email': email.to_email,
                'subject': email.subject[:50] + '...' if len(email.subject) > 50 else email.subject,
                'created_at': email.created_at
            } for email in recent_emails
        ],
        'upcoming_batches': [
            {
                'id': batch.id,
                'name': batch.name,
                'template_name': batch.template.name if batch.template else 'No Template',
                'start_time': batch.start_time,
                'total_recipients': batch.total_recipients
            } for batch in upcoming_batches
        ],
        'email_activity_chart': email_activity,
        'performance_metrics': performance_metrics,
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'plan': tenant.plan,
            'status': tenant.status,
            'max_tenant_admins': tenant.max_tenant_admins,
            'max_staff_admins': tenant.max_staff_admins,
            'max_staff_users': tenant.max_staff_users,
            'max_total_users': tenant.max_total_users,
            'current_user_counts': tenant.current_user_counts,
            'user_usage_percentage': tenant.user_usage_percentage,
            'users_remaining': tenant.users_remaining
        }
    }
    
    # Cache for 2 minutes (shorter cache for tenant-specific data)
    cache.set(cache_key, dashboard_data, 120)
    return dashboard_data


def _get_email_activity_chart_optimized(tenant, start_date):
    """Optimized email activity chart using database aggregation"""
    end_date = timezone.now()
    
    # Use database aggregation instead of looping through days
    from django.db.models import DateField
    from django.db.models.functions import TruncDate
    
    activity_data = EmailLog.objects.filter(
        tenant=tenant,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        sent=Count('id', filter=Q(status='sent')),
        failed=Count('id', filter=Q(status='failed')),
        total=Count('id')
    ).order_by('date')
    
    # Convert to the expected format
    chart_data = []
    for data in activity_data:
        chart_data.append({
            'date': data['date'].isoformat(),
            'sent': data['sent'],
            'failed': data['failed'],
            'total': data['total']
        })
    
    return chart_data


# Keep old function for backward compatibility
def _get_email_activity_chart(tenant, start_date):
    return _get_email_activity_chart_optimized(tenant, start_date)


def _get_performance_metrics_optimized(tenant):
    """Optimized performance metrics using efficient aggregation queries"""
    last_30_days = timezone.now() - timedelta(days=30)
    
    # Get email metrics in single query
    email_metrics = EmailLog.objects.filter(
        tenant=tenant,
        created_at__gte=last_30_days,
        direction='outgoing'  # Only outgoing emails for performance metrics
    ).aggregate(
        total_emails=Count('id')
    )
    
    # Get batch metrics efficiently
    batch_metrics = Batch.objects.filter(
        tenant=tenant,
        created_at__gte=last_30_days
    ).aggregate(
        total_batches=Count('id'),
        total_emails_sent=Sum('emails_sent'),
        avg_emails_per_batch=Avg('emails_sent')
    )
    
    # Get email types distribution
    email_types = EmailLog.objects.filter(
        tenant=tenant,
        created_at__gte=last_30_days,
        direction='outgoing'
    ).values('email_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]  # Limit to top 10
    
    # Get most active templates efficiently
    most_active_templates = _get_most_active_templates_optimized(tenant, last_30_days)
    
    return {
        'emails_last_30_days': email_metrics['total_emails'] or 0,
        'batches_last_30_days': batch_metrics['total_batches'] or 0,
        'avg_emails_per_batch': round(batch_metrics['avg_emails_per_batch'] or 0, 2),
        'email_types_distribution': list(email_types),
        'most_active_templates': most_active_templates
    }


# Keep old function for backward compatibility
def _get_performance_metrics(tenant):
    return _get_performance_metrics_optimized(tenant)


def _get_most_active_templates_optimized(tenant, start_date):
    """Optimized template usage statistics"""
    template_usage = Batch.objects.filter(
        tenant=tenant,
        created_at__gte=start_date,
        template__isnull=False  # Exclude batches without templates
    ).select_related('template').values(
        'template__name'
    ).annotate(
        usage_count=Count('id'),
        total_emails_sent=Sum('emails_sent')
    ).order_by('-usage_count')[:5]
    
    return list(template_usage)


# Keep old function for backward compatibility  
def _get_most_active_templates(tenant, start_date):
    return _get_most_active_templates_optimized(tenant, start_date)


def _get_system_health():
    from django.core.cache import cache
    import redis
    
    health_status = {
        'database': True,
        'redis': True,
        'email_queue': True
    }
    
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
    except Exception:
        health_status['database'] = False
    
    try:
        r = redis.Redis.from_url('redis://localhost:6379/0')
        r.ping()
    except Exception:
        health_status['redis'] = False
    
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if not stats:
            health_status['email_queue'] = False
    except Exception:
        health_status['email_queue'] = False
    
    return health_status


def _get_empty_dashboard():
    return {
        'overview': {
            'total_groups': 0,
            'total_contacts': 0,
            'total_templates': 0,
            'total_batches': 0,
            'active_batches': 0,
            'completed_batches': 0,
            'total_emails_sent': 0,
            'total_emails_failed': 0,
            'pending_emails': 0,
            'success_rate': 0
        },
        'recent_batches': [],
        'recent_email_activity': [],
        'upcoming_batches': [],
        'email_activity_chart': [],
        'performance_metrics': {
            'emails_last_30_days': 0,
            'batches_last_30_days': 0,
            'avg_emails_per_batch': 0,
            'email_types_distribution': [],
            'most_active_templates': []
        }
    }
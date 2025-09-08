from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from .models import User
from tenants.models import Tenant
from batches.models import Batch
from logs.models import EmailLog
from emails.models import EmailTemplate

User = get_user_model()


def get_dashboard_stats(user):
    """
    Get dashboard statistics based on user role
    """
    stats = {}
    
    if user.role in ['super_admin', 'support_team']:
        # Super admin gets global stats
        stats = get_super_admin_dashboard_stats()
    elif user.role in ['tenant_admin', 'staff_admin']:
        # Tenant admin gets tenant-specific stats
        stats = get_tenant_admin_dashboard_stats(user.tenant)
    elif user.role == 'staff':
        # Staff gets limited tenant stats
        stats = get_staff_dashboard_stats(user.tenant)
    else:
        # Default limited stats
        stats = get_basic_dashboard_stats(user.tenant)
    
    return stats


def get_super_admin_dashboard_stats():
    """
    Get comprehensive statistics for super admin
    """
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # Tenant statistics
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(is_active=True).count()
    
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Batch statistics
    total_batches = Batch.objects.count()
    active_batches = Batch.objects.filter(status__in=['scheduled', 'running']).count()
    completed_batches = Batch.objects.filter(status='completed').count()
    
    # Email statistics
    total_emails_sent = EmailLog.objects.filter(status='sent').count()
    emails_sent_today = EmailLog.objects.filter(
        status='sent',
        sent_at__date=today
    ).count()
    emails_sent_30_days = EmailLog.objects.filter(
        status='sent',
        sent_at__date__gte=last_30_days
    ).count()
    
    # Template statistics
    total_templates = EmailTemplate.objects.count()
    active_templates = EmailTemplate.objects.filter(is_active=True).count()
    
    # Recent activity
    recent_batches = Batch.objects.select_related('tenant', 'template').order_by('-created_at')[:5]
    recent_logs = EmailLog.objects.select_related('batch', 'batch__tenant').order_by('-sent_at')[:10]
    
    return {
        'tenant_stats': {
            'total': total_tenants,
            'active': active_tenants,
            'inactive': total_tenants - active_tenants,
        },
        'user_stats': {
            'total': total_users,
            'active': active_users,
            'inactive': total_users - active_users,
        },
        'batch_stats': {
            'total': total_batches,
            'active': active_batches,
            'completed': completed_batches,
            'draft': Batch.objects.filter(status='draft').count(),
            'cancelled': Batch.objects.filter(status='cancelled').count(),
        },
        'email_stats': {
            'total_sent': total_emails_sent,
            'sent_today': emails_sent_today,
            'sent_30_days': emails_sent_30_days,
            'failed': EmailLog.objects.filter(status='failed').count(),
            'pending': EmailLog.objects.filter(status='pending').count(),
        },
        'template_stats': {
            'total': total_templates,
            'active': active_templates,
            'inactive': total_templates - active_templates,
        },
        'recent_activity': {
            'batches': [
                {
                    'id': batch.id,
                    'name': batch.name,
                    'tenant': batch.tenant.name,
                    'status': batch.status,
                    'created_at': batch.created_at,
                }
                for batch in recent_batches
            ],
            'emails': [
                {
                    'id': log.id,
                    'recipient_email': log.recipient_email,
                    'batch_name': log.batch.name if log.batch else 'N/A',
                    'tenant': log.batch.tenant.name if log.batch and log.batch.tenant else 'N/A',
                    'status': log.status,
                    'sent_at': log.sent_at,
                }
                for log in recent_logs
            ],
        }
    }


def get_tenant_admin_dashboard_stats(tenant):
    """
    Get comprehensive statistics for tenant admin
    """
    if not tenant:
        return get_basic_dashboard_stats(None)
    
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    # User statistics for this tenant
    tenant_users = User.objects.filter(tenant=tenant)
    total_users = tenant_users.count()
    active_users = tenant_users.filter(is_active=True).count()
    
    # Batch statistics for this tenant
    tenant_batches = Batch.objects.filter(tenant=tenant)
    total_batches = tenant_batches.count()
    active_batches = tenant_batches.filter(status__in=['scheduled', 'running']).count()
    completed_batches = tenant_batches.filter(status='completed').count()
    
    # Email statistics for this tenant
    tenant_emails = EmailLog.objects.filter(batch__tenant=tenant)
    total_emails_sent = tenant_emails.filter(status='sent').count()
    emails_sent_today = tenant_emails.filter(
        status='sent',
        sent_at__date=today
    ).count()
    emails_sent_30_days = tenant_emails.filter(
        status='sent',
        sent_at__date__gte=last_30_days
    ).count()
    
    # Template statistics for this tenant
    tenant_templates = EmailTemplate.objects.filter(tenant=tenant)
    total_templates = tenant_templates.count()
    active_templates = tenant_templates.filter(is_active=True).count()
    
    # Recent activity for this tenant
    recent_batches = tenant_batches.select_related('template').order_by('-created_at')[:5]
    recent_logs = tenant_emails.select_related('batch').order_by('-sent_at')[:10]
    
    # Documents received stats
    documents_received = tenant_emails.filter(documents_received=True).count()
    documents_pending = tenant_emails.filter(
        status='sent', 
        documents_received=False
    ).count()
    
    return {
        'tenant_info': {
            'name': tenant.name,
            'created_at': tenant.created_at,
            'is_active': tenant.is_active,
        },
        'user_stats': {
            'total': total_users,
            'active': active_users,
            'inactive': total_users - active_users,
            'admins': tenant_users.filter(role__in=['tenant_admin', 'staff_admin']).count(),
            'staff': tenant_users.filter(role='staff').count(),
        },
        'batch_stats': {
            'total': total_batches,
            'active': active_batches,
            'completed': completed_batches,
            'draft': tenant_batches.filter(status='draft').count(),
            'cancelled': tenant_batches.filter(status='cancelled').count(),
        },
        'email_stats': {
            'total_sent': total_emails_sent,
            'sent_today': emails_sent_today,
            'sent_30_days': emails_sent_30_days,
            'failed': tenant_emails.filter(status='failed').count(),
            'pending': tenant_emails.filter(status='pending').count(),
        },
        'template_stats': {
            'total': total_templates,
            'active': active_templates,
            'inactive': total_templates - active_templates,
        },
        'document_stats': {
            'received': documents_received,
            'pending': documents_pending,
            'completion_rate': (documents_received / (documents_received + documents_pending) * 100) if (documents_received + documents_pending) > 0 else 0,
        },
        'recent_activity': {
            'batches': [
                {
                    'id': batch.id,
                    'name': batch.name,
                    'status': batch.status,
                    'total_recipients': batch.total_recipients,
                    'emails_sent': batch.emails_sent,
                    'created_at': batch.created_at,
                }
                for batch in recent_batches
            ],
            'emails': [
                {
                    'id': log.id,
                    'recipient_email': log.recipient_email,
                    'batch_name': log.batch.name if log.batch else 'N/A',
                    'status': log.status,
                    'documents_received': log.documents_received,
                    'sent_at': log.sent_at,
                }
                for log in recent_logs
            ],
        }
    }


def get_staff_dashboard_stats(tenant):
    """
    Get limited statistics for staff users
    """
    if not tenant:
        return get_basic_dashboard_stats(None)
    
    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)
    
    # Limited batch statistics
    tenant_batches = Batch.objects.filter(tenant=tenant)
    active_batches = tenant_batches.filter(status__in=['scheduled', 'running']).count()
    completed_batches = tenant_batches.filter(status='completed').count()
    
    # Limited email statistics
    tenant_emails = EmailLog.objects.filter(batch__tenant=tenant)
    emails_sent_today = tenant_emails.filter(
        status='sent',
        sent_at__date=today
    ).count()
    emails_sent_7_days = tenant_emails.filter(
        status='sent',
        sent_at__date__gte=last_7_days
    ).count()
    
    # Documents received stats
    documents_received_today = tenant_emails.filter(
        documents_received=True,
        documents_received_at__date=today
    ).count()
    documents_pending = tenant_emails.filter(
        status='sent', 
        documents_received=False
    ).count()
    
    # Recent activity (limited)
    recent_batches = tenant_batches.select_related('template').order_by('-created_at')[:3]
    
    return {
        'tenant_info': {
            'name': tenant.name,
        },
        'batch_stats': {
            'active': active_batches,
            'completed': completed_batches,
        },
        'email_stats': {
            'sent_today': emails_sent_today,
            'sent_7_days': emails_sent_7_days,
        },
        'document_stats': {
            'received_today': documents_received_today,
            'pending': documents_pending,
        },
        'recent_batches': [
            {
                'id': batch.id,
                'name': batch.name,
                'status': batch.status,
                'total_recipients': batch.total_recipients,
                'emails_sent': batch.emails_sent,
                'created_at': batch.created_at,
            }
            for batch in recent_batches
        ],
    }


def get_basic_dashboard_stats(tenant):
    """
    Get very basic statistics for limited access
    """
    return {
        'message': 'Limited access - basic stats only',
        'tenant_info': {
            'name': tenant.name if tenant else 'No Tenant',
        },
        'basic_stats': {
            'active_batches': Batch.objects.filter(
                tenant=tenant, 
                status__in=['scheduled', 'running']
            ).count() if tenant else 0,
        }
    }


def get_email_analytics(user, days=30):
    """
    Get email analytics for charts and graphs
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Base queryset based on user role
    if user.role in ['super_admin', 'support_team']:
        email_logs = EmailLog.objects.all()
    elif user.tenant:
        email_logs = EmailLog.objects.filter(batch__tenant=user.tenant)
    else:
        return {}
    
    # Daily email counts
    daily_stats = []
    current_date = start_date
    while current_date <= end_date:
        sent_count = email_logs.filter(
            status='sent',
            sent_at__date=current_date
        ).count()
        failed_count = email_logs.filter(
            status='failed',
            sent_at__date=current_date
        ).count()
        
        daily_stats.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'sent': sent_count,
            'failed': failed_count,
        })
        current_date += timedelta(days=1)
    
    # Status distribution
    status_stats = {
        'sent': email_logs.filter(status='sent').count(),
        'failed': email_logs.filter(status='failed').count(),
        'pending': email_logs.filter(status='pending').count(),
    }
    
    # Documents received stats
    document_stats = {
        'received': email_logs.filter(documents_received=True).count(),
        'pending': email_logs.filter(
            status='sent',
            documents_received=False
        ).count(),
    }
    
    return {
        'daily_stats': daily_stats,
        'status_distribution': status_stats,
        'document_completion': document_stats,
        'period': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'days': days,
        }
    }


def get_batch_performance_analytics(user, batch_id=None):
    """
    Get batch performance analytics
    """
    # Base queryset based on user role
    if user.role in ['super_admin', 'support_team']:
        batches = Batch.objects.all()
    elif user.tenant:
        batches = Batch.objects.filter(tenant=user.tenant)
    else:
        return {}
    
    if batch_id:
        batches = batches.filter(id=batch_id)
    
    batch_stats = []
    for batch in batches.select_related('tenant', 'template')[:20]:  # Limit to 20 for performance
        email_logs = EmailLog.objects.filter(batch=batch)
        
        total_recipients = batch.total_recipients
        emails_sent = email_logs.filter(status='sent').count()
        emails_failed = email_logs.filter(status='failed').count()
        documents_received = email_logs.filter(documents_received=True).count()
        
        success_rate = (emails_sent / total_recipients * 100) if total_recipients > 0 else 0
        completion_rate = (documents_received / emails_sent * 100) if emails_sent > 0 else 0
        
        batch_stats.append({
            'id': batch.id,
            'name': batch.name,
            'tenant': batch.tenant.name if batch.tenant else 'N/A',
            'status': batch.status,
            'total_recipients': total_recipients,
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
            'documents_received': documents_received,
            'success_rate': round(success_rate, 2),
            'completion_rate': round(completion_rate, 2),
            'created_at': batch.created_at,
        })
    
    return {
        'batch_performance': batch_stats,
        'summary': {
            'total_batches': batches.count(),
            'avg_success_rate': sum(b['success_rate'] for b in batch_stats) / len(batch_stats) if batch_stats else 0,
            'avg_completion_rate': sum(b['completion_rate'] for b in batch_stats) / len(batch_stats) if batch_stats else 0,
        }
    }
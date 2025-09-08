"""
🚀 RecallIQ AI-Powered Analytics API Endpoints - Phase 2
✨ Advanced Analytics REST API for Market Domination

These endpoints provide cutting-edge AI analytics that will blow competitors away!
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
import logging

from .ai_analytics import (
    EmailIntelligenceAnalyzer, 
    PredictiveAnalytics, 
    DomainReputationAnalyzer,
    BatchAnalyticsDashboard
)
from .models import Batch
from core.permissions import IsTenantMember

logger = logging.getLogger(__name__)


def check_user_permissions(user, permission_string):
    """
    Simple permission checker for AI analytics
    Returns: (has_permission: bool, error_response: Response or None)
    """
    if not user.is_authenticated:
        return False, Response({
            'success': False,
            'error': 'Authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Allow all authenticated users for now (can be enhanced later)
    return True, None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 15)  # Cache for 15 minutes
@vary_on_headers('Authorization')
def get_ai_analytics_dashboard(request):
    """
    🤖 AI Analytics Dashboard - Complete Intelligence Overview
    
    GET /api/batches/ai-analytics/dashboard/
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 30)
    
    Returns comprehensive AI-powered analytics including:
    - Optimal send time recommendations
    - Recipient engagement patterns
    - Predictive insights
    - Performance trends
    """
    try:
        # Permission check
        has_permission, error_response = check_user_permissions(request.user, 'batches.view_batch')
        if not has_permission:
            return error_response
        
        # Get parameters
        days_back = int(request.GET.get('days_back', 30))
        if days_back > 365:  # Limit to 1 year
            days_back = 365
        
        # Get tenant ID
        tenant_id = getattr(request.user, 'tenant_id', 1)
        
        # Generate comprehensive analytics
        dashboard = BatchAnalyticsDashboard(tenant_id)
        analytics_data = dashboard.get_comprehensive_analytics(days_back)
        
        if 'error' in analytics_data:
            return Response({
                'success': False,
                'error': analytics_data['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'data': analytics_data,
            'message': f'🤖 AI Analytics generated for last {days_back} days'
        })
        
    except ValueError:
        return Response({
            'success': False,
            'error': 'Invalid days_back parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"AI Analytics Dashboard error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to generate analytics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 30)  # Cache for 30 minutes
def get_optimal_send_times(request):
    """
    🕐 AI-Powered Optimal Send Time Analysis
    
    GET /api/batches/ai-analytics/optimal-send-times/
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 30)
    
    Returns AI analysis of optimal send times based on historical engagement
    """
    try:
        has_permission, error_response = check_user_permissions(request.user, 'batches.view_batch')
        if not has_permission:
            return error_response
        
        days_back = int(request.GET.get('days_back', 30))
        tenant_id = getattr(request.user, 'tenant_id', 1)
        
        analyzer = EmailIntelligenceAnalyzer(tenant_id)
        analysis = analyzer.analyze_optimal_send_times(days_back)
        
        return Response({
            'success': True,
            'data': analysis,
            'message': f'🕐 Optimal send times analyzed for last {days_back} days'
        })
        
    except Exception as e:
        logger.error(f"Optimal send times analysis error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to analyze send times'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 20)  # Cache for 20 minutes
def get_recipient_engagement_patterns(request):
    """
    🎯 AI-Powered Recipient Engagement Analysis
    
    GET /api/batches/ai-analytics/engagement-patterns/
    
    Returns intelligent analysis of recipient engagement patterns,
    identifying high-value recipients and engagement trends
    """
    try:
        has_permission, error_response = check_user_permissions(request.user, 'batches.view_batch')
        if not has_permission:
            return error_response
        
        tenant_id = getattr(request.user, 'tenant_id', 1)
        
        analyzer = EmailIntelligenceAnalyzer(tenant_id)
        patterns = analyzer.analyze_recipient_engagement_patterns()
        
        return Response({
            'success': True,
            'data': patterns,
            'message': '🎯 Recipient engagement patterns analyzed'
        })
        
    except Exception as e:
        logger.error(f"Engagement patterns analysis error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to analyze engagement patterns'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_batch_success(request):
    """
    🔮 AI-Powered Batch Success Prediction
    
    POST /api/batches/ai-analytics/predict-success/
    
    Request Body:
    {
        "recipient_count": 1000,
        "scheduled_time": "2025-08-12T14:00:00Z",
        "subject": "Important Update from RecallIQ",
        "content": "Dear recipient, we have an important update...",
        "recipient_emails": ["email1@domain.com", "email2@domain.com", ...]
    }
    
    Returns AI prediction of batch success rate with optimization suggestions
    """
    try:
        has_permission, error_response = check_user_permissions(request.user, 'batches.add_batch')
        if not has_permission:
            return error_response
        
        batch_data = request.data
        tenant_id = getattr(request.user, 'tenant_id', 1)
        
        # Validate required fields
        required_fields = ['recipient_count', 'subject']
        missing_fields = [field for field in required_fields if field not in batch_data]
        if missing_fields:
            return Response({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run prediction
        predictor = PredictiveAnalytics(tenant_id)
        prediction = predictor.predict_batch_success_rate(batch_data)
        
        # Run domain analysis if emails provided
        domain_analysis = None
        if 'recipient_emails' in batch_data:
            domain_analyzer = DomainReputationAnalyzer()
            domain_analysis = domain_analyzer.analyze_recipient_domains(batch_data['recipient_emails'])
        
        response_data = {
            'prediction': prediction,
            'domain_analysis': domain_analysis
        }
        
        return Response({
            'success': True,
            'data': response_data,
            'message': '🔮 Batch success prediction completed'
        })
        
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to predict batch success'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_recipient_domains(request):
    """
    🛡️ AI-Powered Domain Reputation Analysis
    
    POST /api/batches/ai-analytics/analyze-domains/
    
    Request Body:
    {
        "recipient_emails": ["email1@domain.com", "email2@domain.com", ...]
    }
    
    Returns comprehensive domain analysis for deliverability insights
    """
    try:
        has_permission, error_response = check_user_permissions(request.user, 'batches.view_batch')
        if not has_permission:
            return error_response
        
        recipient_emails = request.data.get('recipient_emails', [])
        
        if not recipient_emails:
            return Response({
                'success': False,
                'error': 'recipient_emails list is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(recipient_emails) > 10000:  # Limit for performance
            return Response({
                'success': False,
                'error': 'Maximum 10,000 emails per analysis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        analyzer = DomainReputationAnalyzer()
        analysis = analyzer.analyze_recipient_domains(recipient_emails)
        
        return Response({
            'success': True,
            'data': analysis,
            'message': f'🛡️ Domain analysis completed for {len(recipient_emails)} recipients'
        })
        
    except Exception as e:
        logger.error(f"Domain analysis error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to analyze domains'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_batch_performance_trends(request):
    """
    📈 AI-Powered Batch Performance Trends
    
    GET /api/batches/ai-analytics/performance-trends/
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 30)
    - metric: Specific metric to focus on (success_rate, open_rate, click_rate)
    
    Returns detailed performance trends and insights
    """
    try:
        has_permission, error_response = check_user_permissions(request.user, 'batches.view_batch')
        if not has_permission:
            return error_response
        
        days_back = int(request.GET.get('days_back', 30))
        metric = request.GET.get('metric', 'success_rate')
        tenant_id = getattr(request.user, 'tenant_id', 1)
        
        dashboard = BatchAnalyticsDashboard(tenant_id)
        trends = dashboard._get_batch_performance_trends(days_back)
        
        # Add metric-specific analysis
        if trends.get('daily_trends'):
            metric_values = [day[metric] for day in trends['daily_trends'] if metric in day]
            if metric_values:
                import statistics
                trends['metric_analysis'] = {
                    'metric': metric,
                    'average': round(statistics.mean(metric_values), 2),
                    'max': max(metric_values),
                    'min': min(metric_values),
                    'trend': 'improving' if metric_values[-1] > metric_values[0] else 'declining' if len(metric_values) > 1 else 'stable'
                }
        
        return Response({
            'success': True,
            'data': trends,
            'message': f'📈 Performance trends analyzed for last {days_back} days'
        })
        
    except Exception as e:
        logger.error(f"Performance trends error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get performance trends'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_recommendations(request):
    """
    💡 AI-Powered Optimization Recommendations
    
    GET /api/batches/ai-analytics/recommendations/
    
    Returns personalized AI recommendations for improving email performance
    """
    try:
        has_permission, error_response = check_user_permissions(request.user, 'batches.view_batch')
        if not has_permission:
            return error_response
        
        tenant_id = getattr(request.user, 'tenant_id', 1)
        
        # Gather data for recommendations
        intelligence = EmailIntelligenceAnalyzer(tenant_id)
        dashboard = BatchAnalyticsDashboard(tenant_id)
        
        # Get current performance
        overview = dashboard._get_overview_metrics(30)
        send_times = intelligence.analyze_optimal_send_times(30)
        engagement = intelligence.analyze_recipient_engagement_patterns()
        
        # Generate comprehensive recommendations
        recommendations = []
        
        # Performance-based recommendations
        if overview.get('success_rate', 0) < 80:
            recommendations.append({
                'category': 'Performance',
                'priority': 'high',
                'title': 'Improve Email Deliverability',
                'description': f"Current success rate: {overview.get('success_rate', 0):.1f}%. Focus on email configuration and recipient list quality.",
                'action_items': [
                    'Review SMTP configuration',
                    'Clean recipient list',
                    'Check domain reputation'
                ]
            })
        
        if overview.get('open_rate', 0) < 20:
            recommendations.append({
                'category': 'Engagement',
                'priority': 'high',
                'title': 'Optimize Subject Lines',
                'description': f"Low open rate: {overview.get('open_rate', 0):.1f}%. Improve subject line effectiveness.",
                'action_items': [
                    'A/B test subject lines',
                    'Add personalization',
                    'Optimize send timing'
                ]
            })
        
        # Send time recommendations
        if send_times.get('optimal_hours'):
            best_hour = send_times['optimal_hours'][0]
            recommendations.append({
                'category': 'Timing',
                'priority': 'medium',
                'title': 'Optimize Send Times',
                'description': f"Best performance at {best_hour['hour']}:00 with {best_hour['engagement_score']:.1f}% engagement.",
                'action_items': [
                    f"Schedule batches around {best_hour['hour']}:00",
                    'Test alternative optimal hours',
                    'Consider recipient time zones'
                ]
            })
        
        # Engagement recommendations
        engagement_dist = engagement.get('engagement_distribution', {})
        if engagement_dist.get('low', 0) > engagement_dist.get('high', 0):
            recommendations.append({
                'category': 'Audience',
                'priority': 'medium',
                'title': 'Improve Audience Targeting',
                'description': 'High number of low-engagement recipients detected.',
                'action_items': [
                    'Segment audience by engagement',
                    'Create re-engagement campaigns',
                    'Focus on high-value recipients'
                ]
            })
        
        # General best practices
        recommendations.append({
            'category': 'Best Practices',
            'priority': 'low',
            'title': 'Implement Advanced Features',
            'description': 'Leverage AI-powered features for better results.',
            'action_items': [
                'Use predictive analytics before sending',
                'Monitor real-time performance',
                'Set up automated optimization'
            ]
        })
        
        return Response({
            'success': True,
            'data': {
                'recommendations': recommendations,
                'priority_summary': {
                    'high': len([r for r in recommendations if r['priority'] == 'high']),
                    'medium': len([r for r in recommendations if r['priority'] == 'medium']),
                    'low': len([r for r in recommendations if r['priority'] == 'low'])
                }
            },
            'message': '💡 AI recommendations generated'
        })
        
    except Exception as e:
        logger.error(f"AI recommendations error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to generate recommendations'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_real_time_insights(request):
    """
    ⚡ Real-time AI Insights
    
    GET /api/batches/ai-analytics/real-time-insights/
    
    Returns real-time insights and alerts for ongoing batches
    """
    try:
        has_permission, error_response = check_user_permissions(request.user, 'batches.view_batch')
        if not has_permission:
            return error_response
        
        tenant_id = getattr(request.user, 'tenant_id', 1)
        
        # Get currently running batches
        running_batches = Batch.objects.filter(
            tenant=tenant_id,
            status='RUNNING'
        ).values('id', 'name', 'total_recipients', 'emails_sent', 'emails_failed', 'created_at')
        
        insights = []
        alerts = []
        
        for batch in running_batches:
            batch_id = batch['id']
            total_processed = (batch['emails_sent'] or 0) + (batch['emails_failed'] or 0)
            
            if total_processed > 0:
                success_rate = (batch['emails_sent'] / total_processed) * 100
                
                # Generate insights
                insight = {
                    'batch_id': batch_id,
                    'batch_name': batch['name'],
                    'progress': round((total_processed / batch['total_recipients']) * 100, 1),
                    'current_success_rate': round(success_rate, 1),
                    'status': 'healthy' if success_rate > 80 else 'warning' if success_rate > 60 else 'critical'
                }
                insights.append(insight)
                
                # Generate alerts
                if success_rate < 60:
                    alerts.append({
                        'type': 'critical',
                        'batch_id': batch_id,
                        'message': f"Batch '{batch['name']}' has low success rate: {success_rate:.1f}%",
                        'action': 'Consider pausing batch and reviewing configuration'
                    })
                elif success_rate < 80:
                    alerts.append({
                        'type': 'warning',
                        'batch_id': batch_id,
                        'message': f"Batch '{batch['name']}' performance below optimal: {success_rate:.1f}%",
                        'action': 'Monitor closely and optimize if needed'
                    })
        
        return Response({
            'success': True,
            'data': {
                'insights': insights,
                'alerts': alerts,
                'summary': {
                    'running_batches': len(insights),
                    'critical_alerts': len([a for a in alerts if a['type'] == 'critical']),
                    'warning_alerts': len([a for a in alerts if a['type'] == 'warning'])
                }
            },
            'message': '⚡ Real-time insights generated'
        })
        
    except Exception as e:
        logger.error(f"Real-time insights error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to generate real-time insights'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

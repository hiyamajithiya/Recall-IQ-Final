"""
🤖 RecallIQ AI-Powered Analytics Engine - Phase 2 Deployment
✨ Advanced Intelligence & Optimization for Market Domination

This module contains cutting-edge AI features that will make our application
the most intelligent email platform in the market!
"""

import logging
import json
import statistics
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.core.cache import cache
from collections import defaultdict, Counter
import re

logger = logging.getLogger(__name__)


class EmailIntelligenceAnalyzer:
    """🧠 AI-Powered Email Performance Intelligence"""
    
    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self.cache_timeout = 3600  # 1 hour
    
    def analyze_optimal_send_times(self, days_back: int = 30) -> Dict[str, Any]:
        """
        📊 AI Analysis: Find optimal send times based on historical data
        
        Returns:
            Dict: Optimal send time recommendations
        """
        cache_key = f"optimal_send_times:tenant:{self.tenant_id}:days:{days_back}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            from logs.models import EmailLog
            
            # Get historical email data
            since_date = timezone.now() - timedelta(days=days_back)
            email_logs = EmailLog.objects.filter(
                tenant_id=self.tenant_id,
                created_at__gte=since_date,
                status='sent'
            ).values('created_at', 'opened_at', 'clicked_at')
            
            # Analyze send time patterns
            hourly_stats = defaultdict(lambda: {'sent': 0, 'opened': 0, 'clicked': 0})
            daily_stats = defaultdict(lambda: {'sent': 0, 'opened': 0, 'clicked': 0})
            
            for log in email_logs:
                send_hour = log['created_at'].hour
                send_day = log['created_at'].strftime('%A')
                
                hourly_stats[send_hour]['sent'] += 1
                daily_stats[send_day]['sent'] += 1
                
                if log['opened_at']:
                    hourly_stats[send_hour]['opened'] += 1
                    daily_stats[send_day]['opened'] += 1
                
                if log['clicked_at']:
                    hourly_stats[send_hour]['clicked'] += 1
                    daily_stats[send_day]['clicked'] += 1
            
            # Calculate engagement rates
            best_hours = []
            for hour, stats in hourly_stats.items():
                if stats['sent'] > 10:  # Minimum threshold
                    open_rate = (stats['opened'] / stats['sent']) * 100
                    click_rate = (stats['clicked'] / stats['sent']) * 100
                    engagement_score = (open_rate * 0.7) + (click_rate * 0.3)
                    
                    best_hours.append({
                        'hour': hour,
                        'open_rate': round(open_rate, 2),
                        'click_rate': round(click_rate, 2),
                        'engagement_score': round(engagement_score, 2),
                        'total_sent': stats['sent']
                    })
            
            best_hours.sort(key=lambda x: x['engagement_score'], reverse=True)
            
            # Calculate best days
            best_days = []
            for day, stats in daily_stats.items():
                if stats['sent'] > 5:
                    open_rate = (stats['opened'] / stats['sent']) * 100
                    click_rate = (stats['clicked'] / stats['sent']) * 100
                    engagement_score = (open_rate * 0.7) + (click_rate * 0.3)
                    
                    best_days.append({
                        'day': day,
                        'open_rate': round(open_rate, 2),
                        'click_rate': round(click_rate, 2),
                        'engagement_score': round(engagement_score, 2),
                        'total_sent': stats['sent']
                    })
            
            best_days.sort(key=lambda x: x['engagement_score'], reverse=True)
            
            result = {
                'analysis_period': f"Last {days_back} days",
                'optimal_hours': best_hours[:5],  # Top 5 hours
                'optimal_days': best_days[:3],    # Top 3 days
                'recommendations': self._generate_send_time_recommendations(best_hours, best_days),
                'confidence_level': self._calculate_confidence_level(sum(s['sent'] for s in hourly_stats.values())),
                'generated_at': timezone.now().isoformat()
            }
            
            cache.set(cache_key, result, self.cache_timeout)
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing optimal send times: {str(e)}")
            return {'error': str(e)}
    
    def _generate_send_time_recommendations(self, best_hours: List[Dict], best_days: List[Dict]) -> List[str]:
        """Generate human-readable recommendations"""
        recommendations = []
        
        if best_hours:
            top_hour = best_hours[0]
            if top_hour['hour'] < 12:
                time_desc = f"{top_hour['hour']}:00 AM"
            elif top_hour['hour'] == 12:
                time_desc = "12:00 PM"
            else:
                time_desc = f"{top_hour['hour'] - 12}:00 PM"
            
            recommendations.append(
                f"🕐 Best send time: {time_desc} (engagement: {top_hour['engagement_score']}%)"
            )
        
        if best_days:
            top_day = best_days[0]
            recommendations.append(
                f"📅 Best send day: {top_day['day']} (engagement: {top_day['engagement_score']}%)"
            )
        
        if len(best_hours) >= 2:
            recommendations.append(
                f"⏰ Alternative times: {best_hours[1]['hour']}:00 and {best_hours[2]['hour']}:00"
            )
        
        return recommendations
    
    def _calculate_confidence_level(self, total_emails: int) -> str:
        """Calculate confidence level based on data volume"""
        if total_emails >= 1000:
            return "High (1000+ emails analyzed)"
        elif total_emails >= 100:
            return "Medium (100+ emails analyzed)"
        elif total_emails >= 10:
            return "Low (10+ emails analyzed)"
        else:
            return "Insufficient data (less than 10 emails)"
    
    def analyze_recipient_engagement_patterns(self) -> Dict[str, Any]:
        """
        🎯 AI Analysis: Identify high-value recipients and engagement patterns
        
        Returns:
            Dict: Recipient engagement insights
        """
        cache_key = f"recipient_patterns:tenant:{self.tenant_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            from logs.models import EmailLog
            
            # Get recipient engagement data
            recipient_stats = EmailLog.objects.filter(
                tenant_id=self.tenant_id,
                created_at__gte=timezone.now() - timedelta(days=90)
            ).values('recipient_email').annotate(
                total_emails=Count('id'),
                opened_count=Count('id', filter=Q(opened_at__isnull=False)),
                clicked_count=Count('id', filter=Q(clicked_at__isnull=False))
            ).order_by('-total_emails')
            
            # Categorize recipients
            high_engagement = []
            medium_engagement = []
            low_engagement = []
            
            for recipient in recipient_stats:
                if recipient['total_emails'] >= 3:  # Minimum emails for analysis
                    open_rate = (recipient['opened_count'] / recipient['total_emails']) * 100
                    click_rate = (recipient['clicked_count'] / recipient['total_emails']) * 100
                    
                    recipient_data = {
                        'email': recipient['recipient_email'],
                        'total_emails': recipient['total_emails'],
                        'open_rate': round(open_rate, 1),
                        'click_rate': round(click_rate, 1),
                        'engagement_score': round((open_rate * 0.7) + (click_rate * 0.3), 1)
                    }
                    
                    if recipient_data['engagement_score'] >= 70:
                        high_engagement.append(recipient_data)
                    elif recipient_data['engagement_score'] >= 30:
                        medium_engagement.append(recipient_data)
                    else:
                        low_engagement.append(recipient_data)
            
            # Sort by engagement score
            high_engagement.sort(key=lambda x: x['engagement_score'], reverse=True)
            medium_engagement.sort(key=lambda x: x['engagement_score'], reverse=True)
            low_engagement.sort(key=lambda x: x['engagement_score'], reverse=True)
            
            result = {
                'high_engagement_recipients': high_engagement[:20],  # Top 20
                'medium_engagement_recipients': medium_engagement[:10],  # Top 10
                'low_engagement_recipients': low_engagement[:10],  # Bottom 10
                'engagement_distribution': {
                    'high': len(high_engagement),
                    'medium': len(medium_engagement),
                    'low': len(low_engagement)
                },
                'recommendations': self._generate_engagement_recommendations(
                    len(high_engagement), len(medium_engagement), len(low_engagement)
                ),
                'generated_at': timezone.now().isoformat()
            }
            
            cache.set(cache_key, result, self.cache_timeout)
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing recipient patterns: {str(e)}")
            return {'error': str(e)}
    
    def _generate_engagement_recommendations(self, high: int, medium: int, low: int) -> List[str]:
        """Generate engagement-based recommendations"""
        recommendations = []
        total = high + medium + low
        
        if total == 0:
            return ["📊 Insufficient data for engagement analysis"]
        
        high_pct = (high / total) * 100
        low_pct = (low / total) * 100
        
        if high_pct >= 30:
            recommendations.append(f"🏆 Excellent! {high_pct:.1f}% high-engagement recipients")
        elif high_pct >= 15:
            recommendations.append(f"👍 Good! {high_pct:.1f}% high-engagement recipients")
        else:
            recommendations.append(f"⚠️ Only {high_pct:.1f}% high-engagement recipients - focus on content quality")
        
        if low_pct >= 50:
            recommendations.append("🔄 Consider re-engagement campaigns for low-engagement recipients")
        
        if medium + high > 0:
            recommendations.append(f"🎯 Focus on {medium + high} engaged recipients for best ROI")
        
        return recommendations


class PredictiveAnalytics:
    """🔮 AI-Powered Predictive Analytics Engine"""
    
    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
    
    def predict_batch_success_rate(self, batch_data: Dict) -> Dict[str, Any]:
        """
        🎯 AI Prediction: Estimate batch success rate before sending
        
        Args:
            batch_data: Dictionary containing batch information
            
        Returns:
            Dict: Success rate prediction with confidence
        """
        try:
            # Historical performance data
            historical_data = self._get_historical_batch_performance()
            
            # Feature extraction
            features = self._extract_batch_features(batch_data, historical_data)
            
            # Simple prediction model (can be enhanced with ML)
            predicted_rate = self._calculate_predicted_success_rate(features)
            
            # Risk factors analysis
            risk_factors = self._identify_risk_factors(features)
            
            # Optimization suggestions
            optimizations = self._suggest_optimizations(features, risk_factors)
            
            return {
                'predicted_success_rate': round(predicted_rate, 1),
                'confidence_level': features['confidence'],
                'risk_factors': risk_factors,
                'optimization_suggestions': optimizations,
                'historical_average': round(features['historical_avg'], 1),
                'prediction_factors': {
                    'recipient_count': features['recipient_count'],
                    'time_factor': features['time_factor'],
                    'content_factor': features['content_factor'],
                    'historical_factor': features['historical_factor']
                }
            }
            
        except Exception as e:
            logger.error(f"Error predicting batch success: {str(e)}")
            return {'error': str(e)}
    
    def _get_historical_batch_performance(self) -> Dict[str, float]:
        """Get historical batch performance metrics"""
        try:
            from .models import Batch
            
            recent_batches = Batch.objects.filter(
                tenant=self.tenant_id,
                status='COMPLETED',
                created_at__gte=timezone.now() - timedelta(days=30)
            ).values('emails_sent', 'emails_failed', 'total_recipients')
            
            if not recent_batches:
                return {'avg_success_rate': 85.0, 'total_batches': 0}
            
            success_rates = []
            for batch in recent_batches:
                if batch['total_recipients'] > 0:
                    success_rate = ((batch['emails_sent'] or 0) / batch['total_recipients']) * 100
                    success_rates.append(success_rate)
            
            if success_rates:
                avg_rate = statistics.mean(success_rates)
                return {
                    'avg_success_rate': avg_rate,
                    'total_batches': len(success_rates),
                    'std_deviation': statistics.stdev(success_rates) if len(success_rates) > 1 else 0
                }
            else:
                return {'avg_success_rate': 85.0, 'total_batches': 0}
                
        except Exception as e:
            logger.error(f"Error getting historical performance: {str(e)}")
            return {'avg_success_rate': 85.0, 'total_batches': 0}
    
    def _extract_batch_features(self, batch_data: Dict, historical_data: Dict) -> Dict[str, Any]:
        """Extract features for prediction"""
        # Recipient count factor (larger batches may have lower success rates)
        recipient_count = batch_data.get('recipient_count', 0)
        if recipient_count <= 100:
            count_factor = 1.0
        elif recipient_count <= 500:
            count_factor = 0.95
        elif recipient_count <= 1000:
            count_factor = 0.9
        else:
            count_factor = 0.85
        
        # Time factor (based on optimal send times)
        scheduled_time = batch_data.get('scheduled_time')
        time_factor = self._calculate_time_factor(scheduled_time)
        
        # Content factor (based on subject line and content analysis)
        content_factor = self._analyze_content_quality(batch_data)
        
        # Historical factor
        historical_avg = historical_data['avg_success_rate']
        historical_factor = min(historical_avg / 100, 1.0)
        
        # Confidence calculation
        confidence = "High" if historical_data['total_batches'] >= 10 else \
                    "Medium" if historical_data['total_batches'] >= 3 else "Low"
        
        return {
            'recipient_count': recipient_count,
            'count_factor': count_factor,
            'time_factor': time_factor,
            'content_factor': content_factor,
            'historical_factor': historical_factor,
            'historical_avg': historical_avg,
            'confidence': confidence
        }
    
    def _calculate_time_factor(self, scheduled_time) -> float:
        """Calculate time-based success factor"""
        if not scheduled_time:
            return 0.9  # Default factor for immediate sending
        
        # Business hours (9 AM - 5 PM) typically have better success rates
        hour = scheduled_time.hour
        if 9 <= hour <= 17:
            return 1.0
        elif 6 <= hour <= 9 or 17 <= hour <= 21:
            return 0.95
        else:
            return 0.85
    
    def _analyze_content_quality(self, batch_data: Dict) -> float:
        """Analyze content quality for success prediction"""
        content_score = 1.0
        
        subject = batch_data.get('subject', '')
        content = batch_data.get('content', '')
        
        # Subject line analysis
        if subject:
            # Optimal length
            if 30 <= len(subject) <= 50:
                content_score += 0.05
            elif len(subject) > 70:
                content_score -= 0.1
            
            # Spam indicators
            spam_words = ['free', 'urgent', 'act now', 'limited time', '!!!']
            spam_count = sum(1 for word in spam_words if word.lower() in subject.lower())
            content_score -= spam_count * 0.05
            
            # Personalization indicators
            if any(placeholder in subject for placeholder in ['{name}', '{company}', '{organization}']):
                content_score += 0.1
        
        # Content analysis
        if content:
            # Length factor
            if 100 <= len(content) <= 1000:
                content_score += 0.05
            
            # Call-to-action presence
            cta_indicators = ['click here', 'learn more', 'get started', 'download', 'register']
            if any(cta in content.lower() for cta in cta_indicators):
                content_score += 0.05
        
        return max(0.7, min(1.2, content_score))  # Clamp between 0.7 and 1.2
    
    def _calculate_predicted_success_rate(self, features: Dict) -> float:
        """Calculate predicted success rate using weighted factors"""
        base_rate = features['historical_factor'] * 100
        
        # Apply various factors
        predicted_rate = base_rate * features['count_factor'] * features['time_factor'] * features['content_factor']
        
        # Ensure reasonable bounds
        return max(60.0, min(98.0, predicted_rate))
    
    def _identify_risk_factors(self, features: Dict) -> List[str]:
        """Identify potential risk factors"""
        risks = []
        
        if features['recipient_count'] > 1000:
            risks.append("⚠️ Large recipient count may affect deliverability")
        
        if features['time_factor'] < 0.9:
            risks.append("⏰ Suboptimal send time detected")
        
        if features['content_factor'] < 0.9:
            risks.append("📝 Content quality could be improved")
        
        if features['confidence'] == "Low":
            risks.append("📊 Limited historical data for accurate prediction")
        
        return risks
    
    def _suggest_optimizations(self, features: Dict, risk_factors: List[str]) -> List[str]:
        """Suggest optimizations based on analysis"""
        suggestions = []
        
        if any("time" in risk.lower() for risk in risk_factors):
            suggestions.append("🕐 Consider scheduling during business hours (9 AM - 5 PM)")
        
        if any("content" in risk.lower() for risk in risk_factors):
            suggestions.append("✏️ Improve subject line and add personalization")
            suggestions.append("🎯 Include clear call-to-action in content")
        
        if features['recipient_count'] > 500:
            suggestions.append("📋 Consider segmenting large batches for better deliverability")
        
        if features['historical_factor'] < 0.8:
            suggestions.append("📈 Review and improve email configuration and content strategy")
        
        if not suggestions:
            suggestions.append("✅ Batch configuration looks optimized!")
        
        return suggestions


class DomainReputationAnalyzer:
    """🛡️ AI-Powered Domain & Reputation Analysis"""
    
    def __init__(self):
        self.domain_cache_timeout = 86400  # 24 hours
    
    def analyze_recipient_domains(self, recipient_emails: List[str]) -> Dict[str, Any]:
        """
        🔍 Analyze recipient domains for deliverability insights
        
        Args:
            recipient_emails: List of recipient email addresses
            
        Returns:
            Dict: Domain analysis results
        """
        domain_stats = defaultdict(int)
        risk_domains = []
        enterprise_domains = []
        
        # Known enterprise domains
        trusted_domains = {
            'gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com',
            'microsoft.com', 'google.com', 'apple.com', 'amazon.com'
        }
        
        # Known problematic domains
        suspicious_domains = {
            'tempmail.org', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'throwaway.email'
        }
        
        for email in recipient_emails:
            if '@' in email:
                domain = email.split('@')[1].lower()
                domain_stats[domain] += 1
                
                if domain in suspicious_domains:
                    risk_domains.append(domain)
                elif domain in trusted_domains:
                    enterprise_domains.append(domain)
        
        # Calculate distribution
        total_recipients = len(recipient_emails)
        domain_distribution = []
        
        for domain, count in sorted(domain_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_recipients) * 100
            domain_distribution.append({
                'domain': domain,
                'count': count,
                'percentage': round(percentage, 1),
                'type': self._classify_domain(domain, trusted_domains, suspicious_domains)
            })
        
        return {
            'total_recipients': total_recipients,
            'unique_domains': len(domain_stats),
            'domain_distribution': domain_distribution[:10],  # Top 10 domains
            'risk_assessment': {
                'high_risk_domains': len(set(risk_domains)),
                'enterprise_domains': len(set(enterprise_domains)),
                'risk_percentage': round((len(risk_domains) / total_recipients) * 100, 1) if total_recipients > 0 else 0
            },
            'recommendations': self._generate_domain_recommendations(domain_distribution, len(set(risk_domains)), total_recipients)
        }
    
    def _classify_domain(self, domain: str, trusted: set, suspicious: set) -> str:
        """Classify domain type"""
        if domain in trusted:
            return 'enterprise'
        elif domain in suspicious:
            return 'high_risk'
        elif domain.endswith('.edu'):
            return 'educational'
        elif domain.endswith('.gov'):
            return 'government'
        elif domain.endswith('.org'):
            return 'organization'
        else:
            return 'standard'
    
    def _generate_domain_recommendations(self, distribution: List[Dict], risk_count: int, total: int) -> List[str]:
        """Generate domain-based recommendations"""
        recommendations = []
        
        risk_pct = (risk_count / total) * 100 if total > 0 else 0
        
        if risk_pct > 10:
            recommendations.append(f"⚠️ High risk: {risk_pct:.1f}% suspicious domains detected")
            recommendations.append("🧹 Consider cleaning recipient list before sending")
        elif risk_pct > 5:
            recommendations.append(f"⚠️ Moderate risk: {risk_pct:.1f}% suspicious domains")
        else:
            recommendations.append("✅ Domain distribution looks healthy")
        
        # Check domain concentration
        if distribution and distribution[0]['percentage'] > 50:
            recommendations.append(f"📊 {distribution[0]['percentage']:.1f}% recipients from {distribution[0]['domain']} - consider diversification")
        
        enterprise_pct = sum(d['percentage'] for d in distribution if d['type'] == 'enterprise')
        if enterprise_pct > 70:
            recommendations.append(f"🏆 Excellent! {enterprise_pct:.1f}% enterprise domains")
        
        return recommendations


# 🚀 Enhanced Batch Analytics Dashboard Data Provider
class BatchAnalyticsDashboard:
    """📊 Real-time Analytics Dashboard Data Provider"""
    
    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
    
    def get_comprehensive_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        📈 Get comprehensive analytics for dashboard
        
        Returns:
            Dict: Complete analytics data for dashboard
        """
        try:
            # Initialize analyzers
            intelligence = EmailIntelligenceAnalyzer(self.tenant_id)
            predictive = PredictiveAnalytics(self.tenant_id)
            
            # Gather all analytics
            analytics_data = {
                'overview': self._get_overview_metrics(days_back),
                'optimal_send_times': intelligence.analyze_optimal_send_times(days_back),
                'recipient_engagement': intelligence.analyze_recipient_engagement_patterns(),
                'batch_performance': self._get_batch_performance_trends(days_back),
                'predictive_insights': self._get_predictive_insights(),
                'generated_at': timezone.now().isoformat(),
                'period': f"Last {days_back} days"
            }
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error generating comprehensive analytics: {str(e)}")
            return {'error': str(e)}
    
    def _get_overview_metrics(self, days_back: int) -> Dict[str, Any]:
        """Get overview metrics for the period"""
        try:
            from .models import Batch
            from logs.models import EmailLog
            
            since_date = timezone.now() - timedelta(days=days_back)
            
            # Batch metrics
            total_batches = Batch.objects.filter(
                tenant=self.tenant_id,
                created_at__gte=since_date
            ).count()
            
            completed_batches = Batch.objects.filter(
                tenant=self.tenant_id,
                created_at__gte=since_date,
                status='COMPLETED'
            ).count()
            
            # Email metrics
            total_emails = EmailLog.objects.filter(
                tenant_id=self.tenant_id,
                created_at__gte=since_date
            ).count()
            
            successful_emails = EmailLog.objects.filter(
                tenant_id=self.tenant_id,
                created_at__gte=since_date,
                status='sent'
            ).count()
            
            opened_emails = EmailLog.objects.filter(
                tenant_id=self.tenant_id,
                created_at__gte=since_date,
                opened_at__isnull=False
            ).count()
            
            clicked_emails = EmailLog.objects.filter(
                tenant_id=self.tenant_id,
                created_at__gte=since_date,
                clicked_at__isnull=False
            ).count()
            
            # Calculate rates
            success_rate = (successful_emails / total_emails * 100) if total_emails > 0 else 0
            open_rate = (opened_emails / successful_emails * 100) if successful_emails > 0 else 0
            click_rate = (clicked_emails / successful_emails * 100) if successful_emails > 0 else 0
            
            return {
                'total_batches': total_batches,
                'completed_batches': completed_batches,
                'completion_rate': round((completed_batches / total_batches * 100) if total_batches > 0 else 0, 1),
                'total_emails': total_emails,
                'successful_emails': successful_emails,
                'success_rate': round(success_rate, 1),
                'open_rate': round(open_rate, 1),
                'click_rate': round(click_rate, 1),
                'engagement_score': round((open_rate * 0.7) + (click_rate * 0.3), 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting overview metrics: {str(e)}")
            return {}
    
    def _get_batch_performance_trends(self, days_back: int) -> Dict[str, Any]:
        """Get batch performance trends over time"""
        try:
            from .models import Batch
            
            since_date = timezone.now() - timedelta(days=days_back)
            
            # Daily performance data
            daily_data = defaultdict(lambda: {'batches': 0, 'emails_sent': 0, 'emails_failed': 0})
            
            batches = Batch.objects.filter(
                tenant=self.tenant_id,
                created_at__gte=since_date,
                status='COMPLETED'
            ).values('created_at', 'emails_sent', 'emails_failed')
            
            for batch in batches:
                date_key = batch['created_at'].strftime('%Y-%m-%d')
                daily_data[date_key]['batches'] += 1
                daily_data[date_key]['emails_sent'] += batch['emails_sent'] or 0
                daily_data[date_key]['emails_failed'] += batch['emails_failed'] or 0
            
            # Convert to list format for charts
            trend_data = []
            for date_str in sorted(daily_data.keys()):
                data = daily_data[date_str]
                total_emails = data['emails_sent'] + data['emails_failed']
                success_rate = (data['emails_sent'] / total_emails * 100) if total_emails > 0 else 0
                
                trend_data.append({
                    'date': date_str,
                    'batches': data['batches'],
                    'emails_sent': data['emails_sent'],
                    'emails_failed': data['emails_failed'],
                    'success_rate': round(success_rate, 1)
                })
            
            return {
                'daily_trends': trend_data,
                'total_days': len(trend_data),
                'best_day': max(trend_data, key=lambda x: x['success_rate']) if trend_data else None,
                'worst_day': min(trend_data, key=lambda x: x['success_rate']) if trend_data else None
            }
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {str(e)}")
            return {}
    
    def _get_predictive_insights(self) -> Dict[str, Any]:
        """Get predictive insights for upcoming batches"""
        try:
            from .models import Batch
            
            # Get upcoming scheduled batches
            upcoming_batches = Batch.objects.filter(
                tenant=self.tenant_id,
                status='SCHEDULED',
                scheduled_time__gte=timezone.now()
            ).order_by('scheduled_time')[:5]
            
            predictions = []
            predictive = PredictiveAnalytics(self.tenant_id)
            
            for batch in upcoming_batches:
                batch_data = {
                    'recipient_count': batch.total_recipients,
                    'scheduled_time': batch.scheduled_time,
                    'subject': getattr(batch, 'subject', ''),
                    'content': getattr(batch, 'content', '')
                }
                
                prediction = predictive.predict_batch_success_rate(batch_data)
                predictions.append({
                    'batch_id': batch.id,
                    'batch_name': batch.name,
                    'scheduled_time': batch.scheduled_time.isoformat(),
                    'recipient_count': batch.total_recipients,
                    'predicted_success_rate': prediction.get('predicted_success_rate', 0),
                    'confidence': prediction.get('confidence_level', 'Unknown'),
                    'top_risk': prediction.get('risk_factors', ['None'])[0] if prediction.get('risk_factors') else 'None'
                })
            
            return {
                'upcoming_batch_predictions': predictions,
                'total_upcoming': len(predictions)
            }
            
        except Exception as e:
            logger.error(f"Error getting predictive insights: {str(e)}")
            return {}

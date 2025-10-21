 
from flask import Blueprint, jsonify, request, current_app, session
from api.repositories.calls_repo import CallsRepository
from api.repositories.contacts_repo import ContactsRepository
from api.repositories.feed_repo import FeedRepository
from api.repositories.users_repo import UsersRepository
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

bp = Blueprint("report", __name__)

def require_auth():
    """Check if user is authenticated"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id

@bp.get("")
def index():
    """Get available report types and capabilities"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    return jsonify({
        "ok": True, 
        "endpoint": "report",
        "available_reports": [
            "call_summary",
            "spam_analysis",
            "contact_activity",
            "usage_statistics",
            "security_report",
            "performance_metrics",
            "trend_analysis",
            "custom_report"
        ],
        "supported_formats": ["json", "csv", "pdf"],
        "date_ranges": ["today", "week", "month", "quarter", "year", "custom"]
    })

@bp.get("/call-summary")
def call_summary_report():
    """Generate comprehensive call summary report"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Parse date range
        date_range = request.args.get('range', 'month')
        start_date, end_date = _parse_date_range(date_range)
        
        # Get call data
        calls = calls_repo.get_calls_in_range(user_id, start_date, end_date)
        stats = calls_repo.get_call_statistics(user_id, start_date.isoformat(), end_date.isoformat())
        
        report = {
            "report_type": "call_summary",
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "range": date_range
            },
            "summary": {
                "total_calls": len(calls),
                "incoming_calls": len([c for c in calls if c.get('direction') == 'incoming']),
                "outgoing_calls": len([c for c in calls if c.get('direction') == 'outgoing']),
                "missed_calls": len([c for c in calls if c.get('status') == 'missed']),
                "answered_calls": len([c for c in calls if c.get('status') == 'answered']),
                "total_duration_minutes": sum(c.get('duration_seconds', 0) for c in calls) / 60,
                "average_call_duration": stats.get('avg_duration', 0),
                "spam_calls_detected": len([c for c in calls if c.get('is_spam')])
            },
            "daily_breakdown": _generate_daily_breakdown(calls, start_date, end_date),
            "top_contacts": _get_top_contacts_from_calls(calls),
            "call_patterns": {
                "busiest_hour": _get_busiest_hour(calls),
                "busiest_day": _get_busiest_day(calls),
                "peak_call_times": _get_peak_times(calls)
            }
        }
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating call summary report: {e}")
        return jsonify({"error": "failed to generate call summary report"}), 500

@bp.get("/spam-analysis")
def spam_analysis_report():
    """Generate spam detection and security analysis report"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        
        date_range = request.args.get('range', 'month')
        start_date, end_date = _parse_date_range(date_range)
        
        calls = calls_repo.get_calls_in_range(user_id, start_date, end_date)
        spam_calls = [c for c in calls if c.get('is_spam')]
        
        report = {
            "report_type": "spam_analysis",
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "range": date_range
            },
            "spam_summary": {
                "total_calls": len(calls),
                "spam_calls": len(spam_calls),
                "spam_percentage": (len(spam_calls) / len(calls) * 100) if calls else 0,
                "blocked_calls": len([c for c in spam_calls if c.get('status') == 'blocked']),
                "answered_spam": len([c for c in spam_calls if c.get('status') == 'answered'])
            },
            "spam_patterns": {
                "common_area_codes": _analyze_spam_area_codes(spam_calls),
                "time_patterns": _analyze_spam_timing(spam_calls),
                "duration_patterns": _analyze_spam_duration(spam_calls)
            },
            "security_metrics": {
                "protection_effectiveness": _calculate_protection_effectiveness(calls, spam_calls),
                "false_positive_rate": _estimate_false_positive_rate(calls),
                "risk_score": _calculate_security_risk_score(spam_calls)
            },
            "recommendations": _generate_spam_recommendations(spam_calls, calls)
        }
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating spam analysis report: {e}")
        return jsonify({"error": "failed to generate spam analysis report"}), 500

@bp.get("/contact-activity")
def contact_activity_report():
    """Generate contact interaction and activity report"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        contacts_repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        date_range = request.args.get('range', 'month')
        start_date, end_date = _parse_date_range(date_range)
        
        contacts = contacts_repo.get_all_contacts(user_id)
        calls = calls_repo.get_calls_in_range(user_id, start_date, end_date)
        
        report = {
            "report_type": "contact_activity",
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "range": date_range
            },
            "contact_summary": {
                "total_contacts": len(contacts),
                "active_contacts": len([c for c in contacts if not c.get('is_blocked')]),
                "blocked_contacts": len([c for c in contacts if c.get('is_blocked')]),
                "favorite_contacts": len([c for c in contacts if c.get('is_favorite')])
            },
            "activity_metrics": {
                "contacts_with_calls": _count_contacts_with_activity(contacts, calls),
                "most_active_contacts": _get_most_active_contacts(contacts, calls),
                "least_active_contacts": _get_least_active_contacts(contacts, calls),
                "new_contacts_added": _count_new_contacts(contacts, start_date, end_date)
            },
            "communication_patterns": {
                "average_calls_per_contact": _calculate_avg_calls_per_contact(contacts, calls),
                "contact_response_rates": _calculate_contact_response_rates(calls),
                "preferred_contact_times": _analyze_contact_timing_preferences(calls)
            }
        }
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating contact activity report: {e}")
        return jsonify({"error": "failed to generate contact activity report"}), 500

@bp.get("/usage-statistics")
def usage_statistics_report():
    """Generate comprehensive usage statistics report"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        feed_repo = FeedRepository(cfg.database_url, cfg.queries)
        users_repo = UsersRepository(cfg.database_url, cfg.queries)
        
        date_range = request.args.get('range', 'month')
        start_date, end_date = _parse_date_range(date_range)
        
        user_info = users_repo.get_user(user_id)
        calls = calls_repo.get_calls_in_range(user_id, start_date, end_date)
        feed_stats = feed_repo.get_feed_statistics(user_id)
        
        report = {
            "report_type": "usage_statistics",
            "generated_at": datetime.now().isoformat(),
            "user_info": {
                "user_id": user_id,
                "account_created": user_info.get('created_at') if user_info else None,
                "last_active": user_info.get('last_login') if user_info else None
            },
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "range": date_range
            },
            "call_usage": {
                "total_calls": len(calls),
                "total_minutes": sum(c.get('duration_seconds', 0) for c in calls) / 60,
                "daily_average": len(calls) / ((end_date - start_date).days + 1),
                "peak_usage_day": _get_peak_usage_day(calls),
                "usage_trend": _calculate_usage_trend(calls, start_date, end_date)
            },
            "feature_usage": {
                "spam_detection_triggers": len([c for c in calls if c.get('is_spam')]),
                "call_recordings": len([c for c in calls if c.get('has_recording')]),
                "transcriptions": len([c for c in calls if c.get('transcript')]),
                "feed_items": feed_stats.get('total_items', 0),
                "active_feed_items": feed_stats.get('active_items', 0)
            },
            "performance_metrics": {
                "average_response_time": _calculate_avg_response_time(calls),
                "system_reliability": _calculate_system_reliability(calls),
                "feature_adoption_rate": _calculate_feature_adoption(calls, feed_stats)
            }
        }
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating usage statistics report: {e}")
        return jsonify({"error": "failed to generate usage statistics report"}), 500

@bp.get("/security-report")
def security_report():
    """Generate security and privacy report"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        users_repo = UsersRepository(cfg.database_url, cfg.queries)
        
        date_range = request.args.get('range', 'month')
        start_date, end_date = _parse_date_range(date_range)
        
        user_info = users_repo.get_user(user_id)
        calls = calls_repo.get_calls_in_range(user_id, start_date, end_date)
        
        # Security metrics calculation
        security_events = []
        for call in calls:
            if call.get('is_spam') or call.get('is_blocked'):
                security_events.append(call)
        
        report = {
            "report_type": "security_report",
            "generated_at": datetime.now().isoformat(),
            "user_info": {
                "user_id": user_id,
                "account_created": user_info.get('created_at') if user_info else None,
                "last_active": user_info.get('last_login') if user_info else None
            },
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "range": date_range
            },
            "security_summary": {
                "security_events": len(security_events),
                "spam_detected": len([c for c in calls if c.get('is_spam')]),
                "calls_blocked": len([c for c in calls if c.get('is_blocked')]),
                "security_incidents": len([c for c in calls if c.get('security_alert')])
            },
            "threat_analysis": {
                "common_threat_sources": _analyze_threat_sources(security_events),
                "security_trends": _analyze_security_trends(security_events, start_date, end_date),
                "risk_assessment": _assess_security_risk(security_events)
            },
            "privacy_metrics": {
                "data_access_logs": _get_data_access_logs(user_id, start_date, end_date),
                "privacy_compliance": _check_privacy_compliance(user_info),
                "data_retention": _evaluate_data_retention_policy(user_info)
            },
            "recommendations": _generate_security_recommendations(security_events, user_info)
        }
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating security report: {e}")
        return jsonify({"error": "failed to generate security report"}), 500

# Helper functions (these would need to be implemented based on your specific requirements)
def _parse_date_range(range_str):
    """Parse date range string into start and end dates"""
    today = datetime.now().date()
    
    if range_str == "today":
        start_date = today
        end_date = today
    elif range_str == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif range_str == "month":
        start_date = today.replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
    elif range_str == "quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_start_month, day=1)
        if quarter_start_month == 10:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=quarter_start_month + 3, day=1) - timedelta(days=1)
    elif range_str == "year":
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else:  # custom range
        # For custom ranges, you'd typically parse start/end dates from query parameters
        start_date = today - timedelta(days=30)  # Default to 30 days
        end_date = today
    
    return start_date, end_date

def _generate_daily_breakdown(calls, start_date, end_date):
    """Generate daily breakdown of call data"""
    # Implementation would depend on your specific needs
    return {}

def _get_top_contacts_from_calls(calls):
    """Get top contacts based on call frequency"""
    # Implementation would depend on your specific needs
    return []

def _get_busiest_hour(calls):
    """Determine busiest hour for calls"""
    # Implementation would depend on your specific needs
    return None

def _get_busiest_day(calls):
    """Determine busiest day for calls"""
    # Implementation would depend on your specific needs
    return None

def _get_peak_times(calls):
    """Get peak call times"""
    # Implementation would depend on your specific needs
    return []

def _analyze_spam_area_codes(spam_calls):
    """Analyze area codes in spam calls"""
    # Implementation would depend on your specific needs
    return []

def _analyze_spam_timing(spam_calls):
    """Analyze timing patterns of spam calls"""
    # Implementation would depend on your specific needs
    return []

def _analyze_spam_duration(spam_calls):
    """Analyze duration patterns of spam calls"""
    # Implementation would depend on your specific needs
    return []

def _calculate_protection_effectiveness(all_calls, spam_calls):
    """Calculate spam protection effectiveness"""
    # Implementation would depend on your specific needs
    return 0.0

def _estimate_false_positive_rate(all_calls):
    """Estimate false positive rate"""
    # Implementation would depend on your specific needs
    return 0.0

def _calculate_security_risk_score(spam_calls):
    """Calculate overall security risk score"""
    # Implementation would depend on your specific needs
    return 0.0

def _generate_spam_recommendations(spam_calls, all_calls):
    """Generate spam detection recommendations"""
    # Implementation would depend on your specific needs
    return []

def _count_contacts_with_activity(contacts, calls):
    """Count contacts with call activity"""
    # Implementation would depend on your specific needs
    return 0

def _get_most_active_contacts(contacts, calls):
    """Get most active contacts"""
    # Implementation would depend on your specific needs
    return []

def _get_least_active_contacts(contacts, calls):
    """Get least active contacts"""
    # Implementation would depend on your specific needs
    return []

def _count_new_contacts(contacts, start_date, end_date):
    """Count new contacts added during period"""
    # Implementation would depend on your specific needs
    return 0

def _calculate_avg_calls_per_contact(contacts, calls):
    """Calculate average calls per contact"""
    # Implementation would depend on your specific needs
    return 0.0

def _calculate_contact_response_rates(calls):
    """Calculate contact response rates"""
    # Implementation would depend on your specific needs
    return {}

def _analyze_contact_timing_preferences(calls):
    """Analyze contact timing preferences"""
    # Implementation would depend on your specific needs
    return {}

def _get_peak_usage_day(calls):
    """Get peak usage day"""
    # Implementation would depend on your specific needs
    return None

def _calculate_usage_trend(calls, start_date, end_date):
    """Calculate usage trend"""
    # Implementation would depend on your specific needs
    return []

def _calculate_avg_response_time(calls):
    """Calculate average response time"""
    # Implementation would depend on your specific needs
    return 0.0

def _calculate_system_reliability(calls):
    """Calculate system reliability"""
    # Implementation would depend on your specific needs
    return 0.0

def _calculate_feature_adoption(calls, feed_stats):
    """Calculate feature adoption rate"""
    # Implementation would depend on your specific needs
    return 0.0

def _analyze_threat_sources(security_events):
    """Analyze threat sources"""
    # Implementation would depend on your specific needs
    return []

def _analyze_security_trends(security_events, start_date, end_date):
    """Analyze security trends"""
    # Implementation would depend on your specific needs
    return []

def _assess_security_risk(security_events):
    """Assess overall security risk"""
    # Implementation would depend on your specific needs
    return {}

def _get_data_access_logs(user_id, start_date, end_date):
    """Get data access logs"""
    # Implementation would depend on your specific needs
    return []

def _check_privacy_compliance(user_info):
    """Check privacy compliance"""
    # Implementation would depend on your specific needs
    return True

def _evaluate_data_retention_policy(user_info):
    """Evaluate data retention policy"""
    # Implementation would depend on your specific needs
    return True

def _generate_security_recommendations(security_events, user_info):
    """Generate security recommendations"""
    # Implementation would depend on your specific needs
    return []

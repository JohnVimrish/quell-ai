
from flask import Blueprint, jsonify, request, current_app, session
from api.repositories.calls_repo import CallsRepository
from api.repositories.contacts_repo import ContactsRepository
from api.models.spam_detector import AdvancedSpamDetector as  SpamDetector
from api.utils.validation import contains_sensitive
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

bp = Blueprint("copilot", __name__)  # Changed from "mode" to "copilot"

def require_auth():
    """Check if user is authenticated"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id

@bp.get("")
def index():
    """Get copilot status and capabilities"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        
        return jsonify({
            "ok": True,
            "endpoint": "copilot",
            "capabilities": [
                "call_analysis",
                "spam_detection", 
                "conversation_insights",
                "call_recommendations",
                "real_time_assistance"
            ],
            "ai_providers": list(cfg.providers.keys()) if cfg.providers else []
        })
        
    except Exception as e:
        logger.error(f"Error getting copilot status: {e}")
        return jsonify({"error": "failed to get copilot status"}), 500

@bp.post("/analyze-call")
def analyze_call():
    """Analyze a call for insights and recommendations"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
        
        call_id = data.get('call_id')
        if not call_id:
            return jsonify({"error": "call_id is required"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Get call details
        call = calls_repo.get_call(call_id, user_id)
        if not call:
            return jsonify({"error": "call not found"}), 404
        
        analysis = {
            "call_id": call_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "insights": [],
            "recommendations": [],
            "sentiment": None,
            "key_topics": [],
            "action_items": []
        }
        
        # Spam analysis
        spam_detector = SpamDetector()
        spam_result = spam_detector.analyze_call({
            'from_number': call['from_number'],
            'to_number': call['to_number'],
            'duration_seconds': call.get('duration_seconds', 0),
            'time_of_day': datetime.fromisoformat(call['started_at']).hour if call.get('started_at') else 12
        })
        
        if spam_result.get('is_spam'):
            analysis['insights'].append({
                "type": "spam_detection",
                "confidence": spam_result.get('spam_score', 0),
                "message": "This call has been flagged as potential spam"
            })
            analysis['recommendations'].append({
                "type": "security",
                "priority": "high",
                "action": "Consider blocking this number",
                "reason": "High spam probability detected"
            })
        
        # Transcript analysis if available
        if call.get('transcript'):
            transcript = call['transcript']
            
            # Check for sensitive information
            sensitive_patterns = [
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
            ]
            
            if contains_sensitive(transcript, sensitive_patterns):
                analysis['insights'].append({
                    "type": "privacy_concern",
                    "confidence": 0.9,
                    "message": "Sensitive information detected in conversation"
                })
                analysis['recommendations'].append({
                    "type": "privacy",
                    "priority": "high",
                    "action": "Review transcript for sensitive data",
                    "reason": "Personal information may have been shared"
                })
            
            # Simple sentiment analysis (basic keyword-based)
            positive_words = ['good', 'great', 'excellent', 'happy', 'satisfied', 'thank', 'appreciate']
            negative_words = ['bad', 'terrible', 'awful', 'angry', 'frustrated', 'disappointed', 'problem']
            
            transcript_lower = transcript.lower()
            positive_count = sum(1 for word in positive_words if word in transcript_lower)
            negative_count = sum(1 for word in negative_words if word in transcript_lower)
            
            if positive_count > negative_count:
                analysis['sentiment'] = 'positive'
            elif negative_count > positive_count:
                analysis['sentiment'] = 'negative'
            else:
                analysis['sentiment'] = 'neutral'
            
            # Extract potential action items (simple keyword detection)
            action_keywords = ['follow up', 'call back', 'send', 'email', 'schedule', 'meeting', 'appointment']
            for keyword in action_keywords:
                if keyword in transcript_lower:
                    analysis['action_items'].append({
                        "keyword": keyword,
                        "context": "Detected in conversation",
                        "suggested_action": f"Consider {keyword} as discussed"
                    })
        
        # Call pattern analysis
        if call.get('duration_seconds', 0) < 10:
            analysis['insights'].append({
                "type": "call_pattern",
                "confidence": 0.8,
                "message": "Very short call duration detected"
            })
            analysis['recommendations'].append({
                "type": "follow_up",
                "priority": "medium",
                "action": "Consider following up",
                "reason": "Call was unusually short"
            })
        
        logger.info(f"Call analysis completed for call {call_id}")
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing call: {e}")
        return jsonify({"error": "failed to analyze call"}), 500

@bp.post("/real-time-assist")
def real_time_assist():
    """Provide real-time assistance during an active call"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
        
        phone_number = data.get('phone_number')
        context = data.get('context', '')  # Current conversation context
        
        if not phone_number:
            return jsonify({"error": "phone_number is required"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        contacts_repo = ContactsRepository(cfg.database_url, cfg.queries)
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        
        assistance = {
            "phone_number": phone_number,
            "timestamp": datetime.now().isoformat(),
            "suggestions": [],
            "warnings": [],
            "contact_info": None,
            "call_history": []
        }
        
        # Check if this is a known contact
        contact = contacts_repo.get_by_phone(user_id, phone_number)
        if contact:
            assistance['contact_info'] = {
                "name": contact['name'],
                "company": contact.get('company'),
                "notes": contact.get('notes'),
                "is_blocked": contact.get('is_blocked', False),
                "is_favorite": contact.get('is_favorite', False)
            }
            
            if contact.get('is_blocked'):
                assistance['warnings'].append({
                    "type": "blocked_contact",
                    "message": "This contact is in your blocked list",
                    "priority": "high"
                })
        
        # Get recent call history with this number
        recent_calls = calls_repo.get_calls_by_phone(user_id, phone_number, 1, 5)
        assistance['call_history'] = recent_calls
        
        # Spam check
        spam_detector = SpamDetector()
        spam_result = spam_detector.analyze_call({
            'from_number': phone_number,
            'to_number': 'user',  # Placeholder
            'duration_seconds': 0,
            'time_of_day': datetime.now().hour
        })
        
        if spam_result.get('is_spam'):
            assistance['warnings'].append({
                "type": "spam_risk",
                "message": f"High spam probability ({spam_result.get('spam_score', 0):.2f})",
                "priority": "high"
            })
            assistance['suggestions'].append({
                "type": "security",
                "message": "Consider ending the call if unsolicited",
                "action": "Be cautious with personal information"
            })
        
        # Context-based suggestions
        if context:
            context_lower = context.lower()
            
            # Financial keywords
            financial_keywords = ['credit', 'loan', 'debt', 'payment', 'bank', 'account', 'ssn', 'social security']
            if any(keyword in context_lower for keyword in financial_keywords):
                assistance['warnings'].append({
                    "type": "financial_discussion",
                    "message": "Financial information being discussed",
                    "priority": "medium"
                })
                assistance['suggestions'].append({
                    "type": "privacy",
                    "message": "Avoid sharing sensitive financial details",
                    "action": "Verify caller identity before proceeding"
                })
            
            # Urgency keywords
            urgency_keywords = ['urgent', 'immediate', 'now', 'today', 'expire', 'deadline']
            if any(keyword in context_lower for keyword in urgency_keywords):
                assistance['warnings'].append({
                    "type": "pressure_tactics",
                    "message": "Urgency language detected",
                    "priority": "medium"
                })
                assistance['suggestions'].append({
                    "type": "caution",
                    "message": "Take time to verify urgent requests",
                    "action": "Don't feel pressured to make immediate decisions"
                })
        
        # Time-based suggestions
        current_hour = datetime.now().hour
        if current_hour < 8 or current_hour > 21:  # Outside normal hours
            assistance['warnings'].append({
                "type": "unusual_time",
                "message": "Call received outside normal business hours",
                "priority": "low"
            })
        
        return jsonify(assistance)
        
    except Exception as e:
        logger.error(f"Error providing real-time assistance: {e}")
        return jsonify({"error": "failed to provide assistance"}), 500

@bp.get("/insights")
def get_insights():
    """Get AI-powered insights about call patterns and trends"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Get date range for analysis
        days = int(request.args.get('days', 30))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get call statistics
        stats = calls_repo.get_call_statistics(user_id, start_date.isoformat(), end_date.isoformat())
        
        insights = {
            "period_days": days,
            "total_calls": stats.get('total_calls', 0),
            "spam_calls": stats.get('spam_calls', 0),
            "average_duration": stats.get('avg_duration', 0),
            "sentiment_distribution": stats.get('sentiment_distribution', {}),
            "top_contacts": stats.get('top_contacts', []),
            "trend_analysis": stats.get('trend_analysis', [])
        }
        
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        return jsonify({"error": "failed to get insights"}), 500

@bp.post("/train-model")
def train_model():
    """Train or retrain AI models with user feedback"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
        
        feedback_type = data.get('type')  # 'spam', 'sentiment', 'classification'
        call_id = data.get('call_id')
        correct_label = data.get('correct_label')
        
        if not all([feedback_type, call_id, correct_label]):
            return jsonify({"error": "type, call_id, and correct_label are required"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Verify call belongs to user
        call = calls_repo.get_call(call_id, user_id)
        if not call:
            return jsonify({"error": "call not found"}), 404
        
        # Store feedback for model training
        feedback_data = {
            'user_id': user_id,
            'call_id': call_id,
            'feedback_type': feedback_type,
            'correct_label': correct_label,
            'timestamp': datetime.now().isoformat()
        }
        
        # In a real implementation, this would trigger model retraining
        logger.info(f"Model feedback received: {feedback_data}")
        
        return jsonify({
            "ok": True,
            "message": "Feedback received and will be used for model improvement",
            "feedback_id": f"fb_{call_id}_{feedback_type}"
        })
        
    except Exception as e:
        logger.error(f"Error processing model training feedback: {e}")
        return jsonify({"error": "failed to process feedback"}), 500

@bp.get("/recommendations")
def get_recommendations():
    """Get personalized recommendations based on call history"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        contacts_repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        recommendations = {
            "timestamp": datetime.now().isoformat(),
            "security_recommendations": [],
            "productivity_recommendations": [],
            "contact_recommendations": []
        }
        
        # Get recent call patterns
        recent_calls = calls_repo.get_recent_calls(user_id, 50)
        
        # Security recommendations
        spam_count = sum(1 for call in recent_calls if call.get('is_spam'))
        if spam_count > 5:
            recommendations['security_recommendations'].append({
                "type": "spam_protection",
                "priority": "high",
                "message": f"You've received {spam_count} spam calls recently",
                "action": "Consider enabling enhanced spam filtering"
            })
        
        # Check for frequent unknown numbers
        unknown_numbers = [call for call in recent_calls if not call.get('contact_name')]
        if len(unknown_numbers) > 10:
            recommendations['security_recommendations'].append({
                "type": "unknown_callers",
                "priority": "medium",
                "message": f"{len(unknown_numbers)} calls from unknown numbers",
                "action": "Review and add frequent callers to contacts"
            })
        
        # Productivity recommendations
        short_calls = [call for call in recent_calls if call.get('duration_seconds', 0) < 30]
        if len(short_calls) > 10:
            recommendations['productivity_recommendations'].append({
                "type": "call_efficiency",
                "priority": "medium",
                "message": f"{len(short_calls)} very short calls detected",
                "action": "Consider using voicemail or text for brief communications"
            })
        
        # Contact recommendations
        frequent_numbers = {}
        for call in recent_calls:
            number = call.get('from_number') or call.get('to_number')
            if number and not call.get('contact_name'):
                frequent_numbers[number] = frequent_numbers.get(number, 0) + 1
        
        for number, count in frequent_numbers.items():
            if count >= 3:
                recommendations['contact_recommendations'].append({
                    "type": "add_contact",
                    "priority": "low",
                    "message": f"Frequent calls with {number} ({count} times)",
                    "action": f"Consider adding {number} to contacts",
                    "phone_number": number
                })
        
        return jsonify(recommendations)
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({"error": "failed to get recommendations"}), 500

@bp.post("/voice-command")
def process_voice_command():
    """Process voice commands during calls"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
        
        command = data.get('command', '').lower().strip()
        context = data.get('context', {})
        
        if not command:
            return jsonify({"error": "command is required"}), 400
        
        response = {
            "command": command,
            "understood": False,
            "action": None,
            "response_text": "Command not recognized"
        }
        
        # Process common voice commands
        if "block" in command and "number" in command:
            phone_number = context.get('current_caller')
            if phone_number:
                cfg = current_app.config["APP_CONFIG"]
                contacts_repo = ContactsRepository(cfg.database_url, cfg.queries)
                
                # Add to blocked list or update existing contact
                contact = contacts_repo.get_by_phone(user_id, phone_number)
                if contact:
                    contacts_repo.update_contact(contact['id'], {'is_blocked': True})
                else:
                    contacts_repo.create_contact({
                        'user_id': user_id,
                        'name': f"Blocked {phone_number}",
                        'phone_number': phone_number,
                        'is_blocked': True
                    })
                
                response.update({
                    "understood": True,
                    "action": "block_number",
                    "response_text": f"Number {phone_number} has been blocked"
                })
        
        elif "add" in command and "contact" in command:
            phone_number = context.get('current_caller')
            if phone_number:
                response.update({
                    "understood": True,
                    "action": "add_contact",
                    "response_text": f"Ready to add {phone_number} to contacts. What name should I use?",
                    "next_step": "await_contact_name"
                })
        
        elif "end" in command and "call" in command:
            response.update({
                "understood": True,
                "action": "end_call",
                "response_text": "Ending call now"
            })
        
        elif "record" in command:
            response.update({
                "understood": True,
                "action": "start_recording",
                "response_text": "Call recording started"
            })
        
        elif "stop" in command and "record" in command:
            response.update({
                "understood": True,
                "action": "stop_recording",
                "response_text": "Call recording stopped"
            })
        
        elif "mute" in command:
            response.update({
                "understood": True,
                "action": "mute",
                "response_text": "Microphone muted"
            })
        
        elif "unmute" in command:
            response.update({
                "understood": True,
                "action": "unmute",
                "response_text": "Microphone unmuted"
            })
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing voice command: {e}")
        return jsonify({"error": "failed to process voice command"}), 500

@bp.get("/health")
def health_check():
    """Check health of AI services and models"""
    try:
        cfg = current_app.config["APP_CONFIG"]
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {}
        }
        
        # Check spam detector
        try:
            spam_detector = SpamDetector()
            test_result = spam_detector.analyze_call({
                'from_number': '+1234567890',
                'to_number': '+1987654321',
                'duration_seconds': 30,
                'time_of_day': 12
            })
            health_status['services']['spam_detector'] = {
                "status": "healthy" if test_result is not None else "unhealthy",
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            health_status['services']['spam_detector'] = {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
            health_status['overall_status'] = "degraded"
        
        # Check AI providers
        if cfg.providers:
            for provider_name in cfg.providers.keys():
                health_status['services'][f'ai_provider_{provider_name}'] = {
                    "status": "configured",
                    "last_check": datetime.now().isoformat()
                }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unhealthy",
            "error": str(e)
        }), 500

@bp.post("/feedback")
def submit_feedback():
    """Submit user feedback about AI recommendations"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
        
        feedback_type = data.get('type')  # 'helpful', 'not_helpful', 'incorrect'
        recommendation_id = data.get('recommendation_id')
        comments = data.get('comments', '')
        rating = data.get('rating')  # 1-5 scale
        
        if not feedback_type:
            return jsonify({"error": "feedback type is required"}), 400
        
        feedback_record = {
            'user_id': user_id,
            'feedback_type': feedback_type,
            'recommendation_id': recommendation_id,
            'comments': comments,
            'rating': rating,
            'timestamp': datetime.now().isoformat()
        }
        
        # In a real implementation, store this in a feedback database
        logger.info(f"User feedback received: {feedback_record}")
        
        return jsonify({
            "ok": True,
            "message": "Thank you for your feedback",
            "feedback_id": f"fb_{user_id}_{datetime.now().timestamp()}"
        })
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({"error": "failed to submit feedback"}), 500

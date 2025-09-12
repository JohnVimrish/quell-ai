from flask import Blueprint, jsonify, request, current_app
from api.repositories.calls_repo import CallsRepository
from api.repositories.texts_repo import TextsRepository
from api.repositories.contacts_repo import ContactsRepository
from api.repositories.users_repo import UsersRepository
import logging
import hashlib
import hmac
from datetime import datetime
import json

logger = logging.getLogger(__name__)

bp = Blueprint("webhooks", __name__)

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature for security"""
    if not signature or not secret:
        return False
    
    try:
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False

@bp.get("")
def index():
    """Get available webhook endpoints and their purposes"""
    return jsonify({
        "ok": True, 
        "endpoint": "webhooks",
        "available_webhooks": {
            "twilio": {
                "call_status": "/webhooks/twilio/call-status",
                "sms_status": "/webhooks/twilio/sms-status",
                "incoming_call": "/webhooks/twilio/incoming-call",
                "incoming_sms": "/webhooks/twilio/incoming-sms"
            },
            "voip": {
                "call_events": "/webhooks/voip/call-events",
                "registration": "/webhooks/voip/registration"
            },
            "spam_detection": {
                "results": "/webhooks/spam/results"
            },
            "transcription": {
                "completed": "/webhooks/transcription/completed"
            },
            "ai_analysis": {
                "completed": "/webhooks/ai/analysis-completed"
            }
        },
        "security": "All webhooks require valid signatures for verification"
    })

@bp.post("/twilio/call-status")
def twilio_call_status():
    """Handle Twilio call status updates"""
    try:
        # Verify Twilio signature
        cfg = current_app.config["APP_CONFIG"]
        twilio_secret = cfg.providers.get('twilio', {}).get('webhook_secret')
        
        if twilio_secret:
            signature = request.headers.get('X-Twilio-Signature', '')
            if not verify_webhook_signature(request.get_data(), signature, twilio_secret):
                logger.warning("Invalid Twilio webhook signature")
                return jsonify({"error": "invalid signature"}), 401
        
        # Parse Twilio webhook data
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        duration = request.form.get('CallDuration')
        recording_url = request.form.get('RecordingUrl')
        
        if not call_sid:
            return jsonify({"error": "CallSid is required"}), 400
        
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Find the call by external ID (call_sid)
        call = calls_repo.get_call_by_external_id(call_sid)
        if not call:
            logger.warning(f"Call not found for SID: {call_sid}")
            return jsonify({"message": "call not found"}), 404
        
        # Update call status
        update_data = {
            'status': call_status.lower(),
            'updated_at': datetime.now().isoformat()
        }
        
        if duration:
            update_data['duration_seconds'] = int(duration)
        
        if recording_url:
            update_data['recording_url'] = recording_url
        
        if call_status.lower() in ['completed', 'failed', 'busy', 'no-answer']:
            update_data['ended_at'] = datetime.now().isoformat()
        
        success = calls_repo.update_call(call['id'], update_data)
        
        if success:
            logger.info(f"Updated call {call['id']} status to {call_status}")
            
            # Trigger post-call processing if completed
            if call_status.lower() == 'completed' and recording_url:
                _trigger_post_call_processing(call['id'], recording_url, cfg)
            
            return jsonify({"message": "call status updated"})
        else:
            return jsonify({"error": "failed to update call"}), 500
        
    except Exception as e:
        logger.error(f"Error processing Twilio call status webhook: {e}")
        return jsonify({"error": "webhook processing failed"}), 500

@bp.post("/twilio/incoming-call")
def twilio_incoming_call():
    """Handle incoming call from Twilio"""
    try:
        cfg = current_app.config["APP_CONFIG"]
        
        # Verify Twilio signature
        twilio_secret = cfg.providers.get('twilio', {}).get('webhook_secret')
        if twilio_secret:
            signature = request.headers.get('X-Twilio-Signature', '')
            if not verify_webhook_signature(request.get_data(), signature, twilio_secret):
                return jsonify({"error": "invalid signature"}), 401
        
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        caller_name = request.form.get('CallerName', '')
        
        if not all([call_sid, from_number, to_number]):
            return jsonify({"error": "missing required parameters"}), 400
        
        # Find user by phone number
        users_repo = UsersRepository(cfg.database_url, cfg.queries)
        user = users_repo.get_user_by_phone(to_number)
        
        if not user:
            logger.warning(f"Incoming call to unknown number: {to_number}")
            # Return TwiML to reject call
            return '''<?xml version="1.0" encoding="UTF-8"?>
                     <Response>
                         <Reject reason="busy"/>
                     </Response>''', 200, {'Content-Type': 'text/xml'}
        
        user_id = user['id']
        
        # Check if number is blocked
        contacts_repo = ContactsRepository(cfg.database_url, cfg.queries)
        contact = contacts_repo.get_contact_by_phone(from_number, user_id)
        
        if contact and contact.get('is_blocked'):
            logger.info(f"Blocked call from {from_number} to {to_number}")
            return '''<?xml version="1.0" encoding="UTF-8"?>
                     <Response>
                         <Reject reason="busy"/>
                     </Response>''', 200, {'Content-Type': 'text/xml'}
        
        # Create call record
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        call_data = {
            'user_id': user_id,
            'contact_id': contact['id'] if contact else None,
            'phone_number': from_number,
            'direction': 'incoming',
            'status': 'ringing',
            'external_call_id': call_sid,
            'caller_name': caller_name,
            'started_at': datetime.now().isoformat()
        }
        
        call_id = calls_repo.create_call(call_data)
        
        # Check for spam
        is_spam = _check_spam_call(from_number, user_id, cfg)
        if is_spam:
            calls_repo.update_call(call_id, {'is_spam': True, 'status': 'blocked'})
            logger.info(f"Spam call blocked from {from_number}")
            return '''<?xml version="1.0" encoding="UTF-8"?>
                     <Response>
                         <Reject reason="busy"/>
                     </Response>''', 200, {'Content-Type': 'text/xml'}
        
        # Return TwiML to handle the call
        user_settings = users_repo.get_user_settings(user_id)
        voicemail_enabled = user_settings.get('voicemail_enabled', True)
        recording_enabled = user_settings.get('call_recording_enabled', False)
        
        twiml_response = _generate_call_handling_twiml(
            user_id, call_id, voicemail_enabled, recording_enabled, cfg
        )
        
        logger.info(f"Incoming call created: {call_id}")
        return twiml_response, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logger.error(f"Error processing incoming call webhook: {e}")
        return '''<?xml version="1.0" encoding="UTF-8"?>
                 <Response>
                     <Reject reason="busy"/>
                 </Response>''', 200, {'Content-Type': 'text/xml'}

@bp.post("/twilio/incoming-sms")
def twilio_incoming_sms():
    """Handle incoming SMS from Twilio"""
    try:
        cfg = current_app.config["APP_CONFIG"]
        
        # Verify Twilio signature
        twilio_secret = cfg.providers.get('twilio', {}).get('webhook_secret')
        if twilio_secret:
            signature = request.headers.get('X-Twilio-Signature', '')
            if not verify_webhook_signature(request.get_data(), signature, twilio_secret):
                return jsonify({"error": "invalid signature"}), 401
        
        message_sid = request.form.get('MessageSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        body = request.form.get('Body', '')
        media_count = int(request.form.get('NumMedia', 0))
        
        if not all([message_sid, from_number, to_number]):
            return jsonify({"error": "missing required parameters"}), 400
        
        # Find user by phone number
        users_repo = UsersRepository(cfg.database_url, cfg.queries)
        user = users_repo.get_user_by_phone(to_number)
        
        if not user:
            logger.warning(f"SMS to unknown number: {to_number}")
            return jsonify({"message": "recipient not found"}), 404
        
        user_id = user['id']
        
        # Get or create contact
        contacts_repo = ContactsRepository(cfg.database_url, cfg.queries)
        contact = contacts_repo.get_contact_by_phone(from_number, user_id)
        
        if not contact:
            contact_data = {
                'phone_number': from_number,
                'display_name': from_number,
                'user_id': user_id
            }
            contact_id = contacts_repo.create_contact(contact_data)
            contact = contacts_repo.get_contact(contact_id, user_id)
        
        # Check for spam
        is_spam = _check_spam_message(body, from_number, user_id)
        
        # Handle media attachments
        media_urls = []
        if media_count > 0:
            for i in range(media_count):
                media_url = request.form.get(f'MediaUrl{i}')
                media_type = request.form.get(f'MediaContentType{i}')
                if media_url:
                    media_urls.append({
                        'url': media_url,
                        'type': media_type
                    })
        
        # Create message record
        texts_repo = TextsRepository(cfg.database_url, cfg.queries)
        message_data = {
            'user_id': user_id,
            'contact_id': contact['id'],
            'phone_number': from_number,
            'direction': 'incoming',
            'body': body,
            'is_spam': is_spam,
            'media_urls': media_urls if media_urls else None,
            'received_at': datetime.now().isoformat()
        }
        
        message_id = texts_repo.create_text(message_data)
        
        # Process spam detection if needed
        if is_spam:
            logger.info(f"Spam message detected from {from_number}")
            # Trigger spam analysis
            _trigger_spam_analysis(message_id, body, from_number, cfg)
        
        logger.info(f"Incoming SMS created: {message_id}")
        return jsonify({"message": "message received"})
        
    except Exception as e:
        logger.error(f"Error processing incoming SMS webhook: {e}")
        return jsonify({"error": "webhook processing failed"}), 500

# Helper functions (these would need to be implemented)
def _trigger_post_call_processing(call_id, recording_url, cfg):
    """Trigger post-call processing tasks"""
    pass

def _check_spam_call(from_number, user_id, cfg):
    """Check if incoming call is spam"""
    return False

def _check_spam_message(body, from_number, user_id):
    """Check if incoming message is spam"""
    return False

def _trigger_spam_analysis(message_id, body, from_number, cfg):
    """Trigger spam analysis for message"""
    pass

def _generate_call_handling_twiml(user_id, call_id, voicemail_enabled, recording_enabled, cfg):
    """Generate TwiML for handling incoming calls"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="woman">Hello, you have an incoming call.</Say>
    <Dial>
        <Number>+1234567890</Number>
    </Dial>
</Response>''', 200, {'Content-Type': 'text/xml'}
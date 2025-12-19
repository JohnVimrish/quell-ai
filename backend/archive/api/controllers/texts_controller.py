from flask import Blueprint, jsonify, request, current_app, session
from api.repositories.texts_repo import TextsRepository
from api.repositories.contacts_repo import ContactsRepository
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

bp = Blueprint("texts", __name__)

def require_auth():
    """Check if user is authenticated"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id

def validate_phone_number(phone):
    """Validate phone number format"""
    # Basic phone number validation
    phone_pattern = re.compile(r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4})')
    return phone_pattern.match(re.sub(r'[^\d+]', '', phone))

@bp.get("")
def index():
    """Get available text message endpoints and capabilities"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    return jsonify({
        "ok": True, 
        "endpoint": "texts",
        "capabilities": [
            "send_message",
            "receive_message", 
            "list_conversations",
            "get_conversation",
            "search_messages",
            "bulk_operations",
            "spam_detection",
            "message_analytics"
        ],
        "supported_features": ["read_receipts", "delivery_status", "media_attachments", "group_messaging"]
    })

@bp.get("/conversations")
def list_conversations():
    """Get list of text conversations for the user"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        texts_repo = TextsRepository(cfg.database_url, cfg.queries)
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        
        conversations = texts_repo.get_conversations(user_id, page, limit, include_archived)
        total = texts_repo.count_conversations(user_id, include_archived)
        
        return jsonify({
            "conversations": conversations or [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        return jsonify({"error": "failed to retrieve conversations"}), 500

@bp.get("/conversations/<contact_id>")
def get_conversation(contact_id):
    """Get messages in a specific conversation"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        texts_repo = TextsRepository(cfg.database_url, cfg.queries)
        contacts_repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        # Verify contact belongs to user
        contact = contacts_repo.get_contact(contact_id, user_id)
        if not contact:
            return jsonify({"error": "contact not found"}), 404
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 200)
        
        messages = texts_repo.get_conversation_messages(user_id, contact_id, page, limit)
        total = texts_repo.count_conversation_messages(user_id, contact_id)
        
        # Mark messages as read
        texts_repo.mark_messages_as_read(user_id, contact_id)
        
        return jsonify({
            "contact": contact,
            "messages": messages or [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        return jsonify({"error": "failed to retrieve conversation"}), 500

@bp.post("/send")
def send_message():
    """Send a text message"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "invalid JSON data"}), 400
        
        to_number = payload.get('to_number', '').strip()
        message_body = payload.get('message', '').strip()
        contact_id = payload.get('contact_id')
        
        if not to_number or not message_body:
            return jsonify({"error": "to_number and message are required"}), 400
        
        if not validate_phone_number(to_number):
            return jsonify({"error": "invalid phone number format"}), 400
        
        if len(message_body) > 1600:  # SMS limit
            return jsonify({"error": "message too long (max 1600 characters)"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        texts_repo = TextsRepository(cfg.database_url, cfg.queries)
        contacts_repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        # Get or create contact
        if contact_id:
            contact = contacts_repo.get_contact(contact_id, user_id)
            if not contact:
                return jsonify({"error": "contact not found"}), 404
        else:
            contact = contacts_repo.get_contact_by_phone(to_number, user_id)
            if not contact:
                # Create new contact
                contact_data = {
                    'phone_number': to_number,
                    'display_name': to_number,
                    'user_id': user_id
                }
                contact_id = contacts_repo.create_contact(contact_data)
                contact = contacts_repo.get_contact(contact_id, user_id)
        
        # Check if contact is blocked
        if contact and contact.get('is_blocked'):
            return jsonify({"error": "cannot send message to blocked contact"}), 403
        
        # Create message record
        message_data = {
            'user_id': user_id,
            'contact_id': contact.get('id') if contact else None,
            'phone_number': to_number,
            'message_body': message_body,
            'direction': 'outgoing',
            'status': 'pending',
            'sent_at': datetime.now().isoformat()
        }
        
        message_id = texts_repo.create_message(message_data)
        
        # In a real implementation, you would integrate with SMS provider here
        # For now, we'll simulate successful sending
        texts_repo.update_message_status(message_id, 'sent', datetime.now().isoformat())
        
        message = texts_repo.get_message(message_id)
        
        logger.info(f"Message sent successfully: {message_id}")
        return jsonify({
            "message_id": message_id,
            "status": "sent",
            "message": message
        }), 201
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({"error": "failed to send message"}), 500

@bp.post("/receive")
def receive_message():
    """Webhook endpoint for receiving incoming messages"""
    # This would typically be called by your SMS provider
    try:
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "invalid JSON data"}), 400
        
        from_number = payload.get('from_number', '').strip()
        to_number = payload.get('to_number', '').strip()
        message_body = payload.get('message', '').strip()
        received_at = payload.get('received_at', datetime.now().isoformat())
        
        if not all([from_number, to_number, message_body]):
            return jsonify({"error": "from_number, to_number, and message are required"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        texts_repo = TextsRepository(cfg.database_url, cfg.queries)
        contacts_repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        # Find user by phone number
        user = texts_repo.get_user_by_phone(to_number)
        if not user:
            logger.warning(f"Received message for unknown number: {to_number}")
            return jsonify({"error": "recipient not found"}), 404
        
        user_id = user.get('id')
        
        # Get or create contact
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
        is_spam = _detect_spam_message(message_body, from_number, user_id)
        
        # Create message record
        message_data = {
            'user_id': user_id,
            'contact_id': contact.get('id'),
            'phone_number': from_number,
            'message_body': message_body,
            'direction': 'incoming',
            'status': 'received',
            'is_spam': is_spam,
            'received_at': received_at
        }
        
        message_id = texts_repo.create_message(message_data)
        
        # If spam, auto-block or flag
        if is_spam:
            _handle_spam_message(user_id, contact.get('id'), message_id, cfg)
        
        logger.info(f"Message received: {message_id} (spam: {is_spam})")
        return jsonify({
            "message_id": message_id,
            "status": "received",
            "spam_detected": is_spam
        }), 201
        
    except Exception as e:
        logger.error(f"Error receiving message: {e}")
        return jsonify({"error": "failed to process incoming message"}), 500

@bp.get("/search")
def search_messages():
    """Search messages by content"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({"error": "search query is required"}), 400
        
        if len(query) < 2:
            return jsonify({"error": "search query must be at least 2 characters"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        texts_repo = TextsRepository(cfg.database_url, cfg.queries)
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        contact_id = request.args.get('contact_id')
        
        results = texts_repo.search_messages(user_id, query, page, limit, contact_id)
        total = texts_repo.count_search_results(user_id, query, contact_id)
        
        return jsonify({
            "query": query,
            "results": results or [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        return jsonify({"error": "failed to search messages"}), 500

def _detect_spam_message(message_body, from_number, user_id):
    """Detect spam messages based on patterns"""
    # Simple spam detection logic
    spam_patterns = [
        r'\b(offer|deal|free|win|prize|cash|money|urgent|limited time)\b',
        r'\$\d+',
        r'click here|visit now|call now'
    ]
    
    message_lower = message_body.lower()
    for pattern in spam_patterns:
        if re.search(pattern, message_lower):
            return True
    return False

def _handle_spam_message(user_id, contact_id, message_id, config):
    """Handle spam messages (block contact, flag, etc.)"""
    try:
        texts_repo = TextsRepository(config.database_url, config.queries)
        contacts_repo = ContactsRepository(config.database_url, config.queries)
        
        # Block the contact
        contacts_repo.update_contact(contact_id, {'is_blocked': True})
        
        # Flag message as spam
        texts_repo.update_message_spam_status(message_id, True)
        
        logger.info(f"Spam message handled for contact {contact_id}")
    except Exception as e:
        logger.error(f"Error handling spam message: {e}")
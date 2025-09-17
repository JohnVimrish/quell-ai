
from flask import Blueprint, jsonify, request, current_app, session
from datetime import datetime, timedelta
from api.repositories.calls_repo import CallsRepository
from api.models.spam_detector import AdvancedSpamDetector as SpamDetector
from api.utils.validation import contains_sensitive
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("calls", __name__)

def require_auth():
    """Check if user is authenticated"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id

@bp.get("")
def index():
    """List user's calls with pagination and filtering"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Query parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 per page
        call_type = request.args.get('type')  # 'incoming', 'outgoing'
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        
        # Build filters
        filters = {'user_id': user_id}
        if call_type:
            filters['call_type'] = call_type
        if date_from:
            filters['date_from'] = datetime.fromisoformat(date_from)
        if date_to:
            filters['date_to'] = datetime.fromisoformat(date_to)
        
        calls = repo.list_calls(filters, page, limit)
        total = repo.count_calls(filters)
        
        return jsonify({
            "calls": calls,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing calls: {e}")
        return jsonify({"error": "failed to retrieve calls"}), 500

@bp.get("/<int:call_id>")
def get_call(call_id):
    """Get specific call details"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        call = repo.get_call(call_id, user_id)
        if not call:
            return jsonify({"error": "call not found"}), 404
        
        return jsonify(call)
        
    except Exception as e:
        logger.error(f"Error getting call {call_id}: {e}")
        return jsonify({"error": "failed to retrieve call"}), 500

@bp.post("")
def create_call():
    """Create a new call record"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
        
        # Required fields
        required_fields = ['from_number', 'to_number', 'call_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Spam detection
        spam_detector = SpamDetector()
        spam_result = spam_detector.analyze_call({
            'from_number': data['from_number'],
            'to_number': data['to_number'],
            'duration_seconds': data.get('duration_seconds', 0),
            'time_of_day': datetime.now().hour
        })
        
        call_data = {
            'user_id': user_id,
            'from_number': data['from_number'],
            'to_number': data['to_number'],
            'call_type': data['call_type'],
            'duration_seconds': data.get('duration_seconds', 0),
            'status': data.get('status', 'completed'),
            'recording_url': data.get('recording_url'),
            'transcript': data.get('transcript'),
            'spam_score': spam_result.get('spam_score', 0.0),
            'is_spam': spam_result.get('is_spam', False),
            'started_at': data.get('started_at', datetime.now()),
            'ended_at': data.get('ended_at')
        }
        
        call = repo.create_call(call_data)
        logger.info(f"Call created: {call['id']} for user {user_id}")
        
        return jsonify(call), 201
        
    except Exception as e:
        logger.error(f"Error creating call: {e}")
        return jsonify({"error": "failed to create call"}), 500

@bp.put("/<int:call_id>")
def update_call(call_id):
    """Update call details"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Check if call exists and belongs to user
        existing_call = repo.get_call(call_id, user_id)
        if not existing_call:
            return jsonify({"error": "call not found"}), 404
        
        # Update allowed fields
        update_data = {}
        allowed_fields = ['status', 'recording_url', 'transcript', 'notes', 'ended_at']
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if update_data:
            call = repo.update_call(call_id, update_data)
            return jsonify(call)
        else:
            return jsonify({"error": "no valid fields to update"}), 400
        
    except Exception as e:
        logger.error(f"Error updating call {call_id}: {e}")
        return jsonify({"error": "failed to update call"}), 500

@bp.delete("/<int:call_id>")
def delete_call(call_id):
    """Delete a call record"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Check if call exists and belongs to user
        existing_call = repo.get_call(call_id, user_id)
        if not existing_call:
            return jsonify({"error": "call not found"}), 404
        
        repo.delete_call(call_id)
        logger.info(f"Call deleted: {call_id} by user {user_id}")
        
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error deleting call {call_id}: {e}")
        return jsonify({"error": "failed to delete call"}), 500

@bp.get("/stats")
def get_call_stats():
    """Get call statistics for the user"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Get stats for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        stats = repo.get_call_stats(user_id, start_date, end_date)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting call stats: {e}")
        return jsonify({"error": "failed to retrieve stats"}), 500

@bp.post("/<int:call_id>/mark-spam")
def mark_spam(call_id):
    """Mark a call as spam"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        call = repo.get_call(call_id, user_id)
        if not call:
            return jsonify({"error": "call not found"}), 404
        
        repo.update_call(call_id, {'is_spam': True, 'spam_score': 1.0})
        
        # Train spam detector with this feedback
        spam_detector = SpamDetector()
        spam_detector.add_feedback(call['from_number'], True)
        
        logger.info(f"Call {call_id} marked as spam by user {user_id}")
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error marking call as spam: {e}")
        return jsonify({"error": "failed to mark as spam"}), 500

@bp.post("/<int:call_id>/mark-not-spam")
def mark_not_spam(call_id):
    """Mark a call as not spam"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        call = repo.get_call(call_id, user_id)
        if not call:
            return jsonify({"error": "call not found"}), 404
        
        repo.update_call(call_id, {'is_spam': False, 'spam_score': 0.0})
        
        # Train spam detector with this feedback
        spam_detector = SpamDetector()
        spam_detector.add_feedback(call['from_number'], False)
        
        logger.info(f"Call {call_id} marked as not spam by user {user_id}")
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error marking call as not spam: {e}")
        return jsonify({"error": "failed to mark as not spam"}), 500

@bp.get("/recent")
def get_recent_calls():
    """Get recent calls (last 24 hours)"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        # Get calls from last 24 hours
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)
        
        filters = {
            'user_id': user_id,
            'date_from': start_date,
            'date_to': end_date
        }
        
        calls = repo.list_calls(filters, 1, 20)  # Last 20 calls
        
        return jsonify({"calls": calls})
        
    except Exception as e:
        logger.error(f"Error getting recent calls: {e}")
        return jsonify({"error": "failed to retrieve recent calls"}), 500

@bp.get("/spam")
def get_spam_calls():
    """Get all spam calls for the user"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        filters = {'user_id': user_id, 'is_spam': True}
        calls = repo.list_calls(filters, page, limit)
        total = repo.count_calls(filters)
        
        return jsonify({
            "calls": calls,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting spam calls: {e}")
        return jsonify({"error": "failed to retrieve spam calls"}), 500

@bp.post("/<int:call_id>/transcript")
def update_transcript(call_id):
    """Update call transcript"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data or 'transcript' not in data:
            return jsonify({"error": "transcript is required"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        call = repo.get_call(call_id, user_id)
        if not call:
            return jsonify({"error": "call not found"}), 404
        
        # Check for sensitive information in transcript
        sensitive_patterns = [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
        ]
        
        transcript = data['transcript']
        if contains_sensitive(transcript, sensitive_patterns):
            logger.warning(f"Sensitive information detected in transcript for call {call_id}")
        
        repo.update_call(call_id, {'transcript': transcript})
        
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error updating transcript: {e}")
        return jsonify({"error": "failed to update transcript"}), 500

@bp.post("/<int:call_id>/notes")
def add_notes(call_id):
    """Add or update notes for a call"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data or 'notes' not in data:
            return jsonify({"error": "notes are required"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        call = repo.get_call(call_id, user_id)
        if not call:
            return jsonify({"error": "call not found"}), 404
        
        repo.update_call(call_id, {'notes': data['notes']})
        
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error adding notes: {e}")
        return jsonify({"error": "failed to add notes"}), 500

@bp.get("/search")
def search_calls():
    """Search calls by phone number or transcript content"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({"error": "search query is required"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        calls = repo.search_calls(user_id, query, page, limit)
        total = repo.count_search_results(user_id, query)
        
        return jsonify({
            "calls": calls,
            "query": query,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching calls: {e}")
        return jsonify({"error": "failed to search calls"}), 500

@bp.post("/bulk-delete")
def bulk_delete_calls():
    """Delete multiple calls at once"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data or 'call_ids' not in data:
            return jsonify({"error": "call_ids array is required"}), 400
        
        call_ids = data['call_ids']
        if not isinstance(call_ids, list) or len(call_ids) == 0:
            return jsonify({"error": "call_ids must be a non-empty array"}), 400
        
        if len(call_ids) > 100:  # Limit bulk operations
            return jsonify({"error": "cannot delete more than 100 calls at once"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        deleted_count = repo.bulk_delete_calls(user_id, call_ids)
        
        logger.info(f"Bulk deleted {deleted_count} calls for user {user_id}")
        return jsonify({"deleted_count": deleted_count})
        
    except Exception as e:
        logger.error(f"Error bulk deleting calls: {e}")
        return jsonify({"error": "failed to delete calls"}), 500

@bp.post("/export")
def export_calls():
    """Export calls to CSV format"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True) or {}
        
        # Date range for export
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        cfg = current_app.config["APP_CONFIG"]
        repo = CallsRepository(cfg.database_url, cfg.queries)
        
        filters = {'user_id': user_id}
        if date_from:
            filters['date_from'] = datetime.fromisoformat(date_from)
        if date_to:
            filters['date_to'] = datetime.fromisoformat(date_to)
        
        # Get all calls for export (no pagination)
        calls = repo.list_calls(filters, 1, 10000)  # Large limit for export
        
        # Generate CSV data
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # CSV headers
        writer.writerow([
            'ID', 'From Number', 'To Number', 'Call Type', 'Duration (seconds)',
            'Status', 'Started At', 'Ended At', 'Is Spam', 'Spam Score', 'Notes'
        ])
        
        # CSV data
        for call in calls:
            writer.writerow([
                call.get('id'),
                call.get('from_number'),
                call.get('to_number'),
                call.get('call_type'),
                call.get('duration_seconds'),
                call.get('status'),
                call.get('started_at'),
                call.get('ended_at'),
                call.get('is_spam'),
                call.get('spam_score'),
                call.get('notes', '')
            ])
        
        csv_data = output.getvalue()
        output.close()
        
        return jsonify({
            "csv_data": csv_data,
            "filename": f"calls_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "total_records": len(calls)
        })
        
    except Exception as e:
        logger.error(f"Error exporting calls: {e}")
        return jsonify({"error": "failed to export calls"}), 500

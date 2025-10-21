from flask import Blueprint, jsonify, request, current_app, session
from api.repositories.contacts_repo import ContactsRepository
from api.utils.validation import contains_sensitive
import logging
import re
 
logger = logging.getLogger(__name__)

bp = Blueprint("contacts", __name__)

def require_auth():
    """Check if user is authenticated"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id

def validate_phone_number(phone):
    """Validate phone number format"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False
    
    return True

def format_phone_number(phone):
    """Format phone number consistently"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Format as +1XXXXXXXXXX for US numbers (10 digits)
    if len(digits_only) == 10:
        return f"+1{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        return f"+{digits_only}"
    else:
        return f"+{digits_only}"

@bp.get("")
def index():
    """List user's contacts with pagination and filtering"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        # Query parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 per page
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'name')  # name, created_at, last_contacted
        
        contacts = repo.list_contacts(user_id, page, limit, search, sort_by)
        total = repo.count_contacts(user_id, search)
        
        return jsonify({
            "contacts": contacts,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing contacts: {e}")
        return jsonify({"error": "failed to retrieve contacts"}), 500

@bp.get("/<int:contact_id>")
def get_contact(contact_id):
    """Get specific contact details"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        contact = repo.get_contact(contact_id, user_id)
        if not contact:
            return jsonify({"error": "contact not found"}), 404
        
        return jsonify(contact)
        
    except Exception as e:
        logger.error(f"Error getting contact {contact_id}: {e}")
        return jsonify({"error": "failed to retrieve contact"}), 500

@bp.post("")
def create_contact():
    """Create a new contact"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
        
        # Required fields
        name = data.get('name', '').strip()
        phone_number = data.get('phone_number', '').strip()
        
        if not name:
            return jsonify({"error": "name is required"}), 400
        
        if not phone_number:
            return jsonify({"error": "phone_number is required"}), 400
        
        # Validate phone number
        if not validate_phone_number(phone_number):
            return jsonify({"error": "invalid phone number format"}), 400
        
        # Format phone number consistently
        formatted_phone = format_phone_number(phone_number)
        
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        # Check if contact with this phone number already exists for user
        existing_contact = repo.get_by_phone(user_id, formatted_phone)
        if existing_contact:
            return jsonify({"error": "contact with this phone number already exists"}), 409
        
        contact_data = {
            'user_id': user_id,
            'name': name,
            'phone_number': formatted_phone,
            'email': data.get('email', '').strip(),
            'company': data.get('company', '').strip(),
            'notes': data.get('notes', '').strip(),
            'is_blocked': data.get('is_blocked', False),
            'is_favorite': data.get('is_favorite', False),
            'tags': data.get('tags', [])
        }
        
        # Validate email if provided
        if contact_data['email']:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, contact_data['email']):
                return jsonify({"error": "invalid email format"}), 400
        
        contact = repo.create_contact(contact_data)
        logger.info(f"Contact created: {contact['id']} for user {user_id}")
        
        return jsonify(contact), 201
        
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        return jsonify({"error": "failed to create contact"}), 500

@bp.put("/<int:contact_id>")
def update_contact(contact_id):
    """Update contact details"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        # Check if contact exists and belongs to user
        existing_contact = repo.get_contact(contact_id, user_id)
        if not existing_contact:
            return jsonify({"error": "contact not found"}), 404
        
        # Update allowed fields
        update_data = {}
        allowed_fields = ['name', 'phone_number', 'email', 'company', 'notes', 'is_blocked', 'is_favorite', 'tags']
        
        for field in allowed_fields:
            if field in data:
                value = data[field]
                
                # Special validation for specific fields
                if field == 'phone_number' and value:
                    if not validate_phone_number(value):
                        return jsonify({"error": "invalid phone number format"}), 400
                    value = format_phone_number(value)
                    
                    # Check if another contact has this phone number
                    existing_phone = repo.get_by_phone(user_id, value)
                    if existing_phone and existing_phone['id'] != contact_id:
                        return jsonify({"error": "another contact with this phone number already exists"}), 409
                
                elif field == 'email' and value:
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, value):
                        return jsonify({"error": "invalid email format"}), 400
                
                elif field == 'name' and not value.strip():
                    return jsonify({"error": "name cannot be empty"}), 400
                
                update_data[field] = value
        
        if update_data:
            contact = repo.update_contact(contact_id, update_data)
            return jsonify(contact)
        else:
            return jsonify({"error": "no valid fields to update"}), 400
        
    except Exception as e:
        logger.error(f"Error updating contact {contact_id}: {e}")
        return jsonify({"error": "failed to update contact"}), 500

@bp.delete("/<int:contact_id>")
def delete_contact(contact_id):
    """Delete a contact"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        # Check if contact exists and belongs to user
        existing_contact = repo.get_contact(contact_id, user_id)
        if not existing_contact:
            return jsonify({"error": "contact not found"}), 404
        
        repo.delete_contact(contact_id)
        logger.info(f"Contact deleted: {contact_id} by user {user_id}")
        
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error deleting contact {contact_id}: {e}")
        return jsonify({"error": "failed to delete contact"}), 500

@bp.post("/<int:contact_id>/block")
def block_contact(contact_id):
    """Block a contact"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        contact = repo.get_contact(contact_id, user_id)
        if not contact:
            return jsonify({"error": "contact not found"}), 404
        
        repo.update_contact(contact_id, {'is_blocked': True})
        
        logger.info(f"Contact {contact_id} blocked by user {user_id}")
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error blocking contact: {e}")
        return jsonify({"error": "failed to block contact"}), 500

@bp.post("/<int:contact_id>/unblock")
def unblock_contact(contact_id):
    """Unblock a contact"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        contact = repo.get_contact(contact_id, user_id)
        if not contact:
            return jsonify({"error": "contact not found"}), 404
        
        repo.update_contact(contact_id, {'is_blocked': False})
        
        logger.info(f"Contact {contact_id} unblocked by user {user_id}")
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error unblocking contact: {e}")
        return jsonify({"error": "failed to unblock contact"}), 500

@bp.post("/<int:contact_id>/favorite")
def add_to_favorites(contact_id):
    """Add contact to favorites"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        contact = repo.get_contact(contact_id, user_id)
        if not contact:
            return jsonify({"error": "contact not found"}), 404
        
        repo.update_contact(contact_id, {'is_favorite': True})
        
        logger.info(f"Contact {contact_id} added to favorites by user {user_id}")
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error adding contact to favorites: {e}")
        return jsonify({"error": "failed to add contact to favorites"}), 500

@bp.post("/<int:contact_id>/unfavorite")
def remove_from_favorites(contact_id):
    """Remove contact from favorites"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        contact = repo.get_contact(contact_id, user_id)
        if not contact:
            return jsonify({"error": "contact not found"}), 404
        
        repo.update_contact(contact_id, {'is_favorite': False})
        
        logger.info(f"Contact {contact_id} removed from favorites by user {user_id}")
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Error removing contact from favorites: {e}")
        return jsonify({"error": "failed to remove contact from favorites"}), 500

@bp.get("/favorites")
def get_favorites():
    """Get all favorite contacts"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        contacts = repo.get_favorites(user_id, page, limit)
        total = repo.count_favorites(user_id)
        
        return jsonify({
            "contacts": contacts,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting favorite contacts: {e}")
        return jsonify({"error": "failed to retrieve favorite contacts"}), 500

@bp.get("/blocked")
def get_blocked():
    """Get all blocked contacts"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        contacts = repo.get_blocked(user_id, page, limit)
        total = repo.count_blocked(user_id)
        
        return jsonify({
            "contacts": contacts,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting blocked contacts: {e}")
        return jsonify({"error": "failed to retrieve blocked contacts"}), 500

@bp.get("/search")
def search_contacts():
    """Search contacts by name, phone, or email"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({"error": "search query is required"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        contacts = repo.search_contacts(user_id, query, page, limit)
        total = repo.count_search_results(user_id, query)
        
        return jsonify({
            "contacts": contacts,
            "query": query,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching contacts: {e}")
        return jsonify({"error": "failed to search contacts"}), 500

@bp.post("/bulk-delete")
def bulk_delete_contacts():
    """Delete multiple contacts at once"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data or 'contact_ids' not in data:
            return jsonify({"error": "contact_ids array is required"}), 400
        
        contact_ids = data['contact_ids']
        if not isinstance(contact_ids, list) or len(contact_ids) == 0:
            return jsonify({"error": "contact_ids must be a non-empty array"}), 400
        
        if len(contact_ids) > 100:  # Limit bulk operations
            return jsonify({"error": "cannot delete more than 100 contacts at once"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        deleted_count = repo.bulk_delete_contacts(user_id, contact_ids)
        
        logger.info(f"Bulk deleted {deleted_count} contacts for user {user_id}")
        return jsonify({"deleted_count": deleted_count})
        
    except Exception as e:
        logger.error(f"Error bulk deleting contacts: {e}")
        return jsonify({"error": "failed to delete contacts"}), 500

@bp.post("/import")
def import_contacts():
    """Import contacts from CSV data"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        data = request.get_json(force=True)
        if not data or 'csv_data' not in data:
            return jsonify({"error": "csv_data is required"}), 400
        
        import csv
        import io
        
        csv_data = data['csv_data']
        csv_file = io.StringIO(csv_data)
        reader = csv.DictReader(csv_file)
        
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
            try:
                name = row.get('name', '').strip()
                phone = row.get('phone_number', '').strip()
                
                if not name or not phone:
                    errors.append(f"Row {row_num}: name and phone_number are required")
                    continue
                
                if not validate_phone_number(phone):
                    errors.append(f"Row {row_num}: invalid phone number format")
                    continue
                
                formatted_phone = format_phone_number(phone)
                
                # Check if contact already exists
                existing = repo.get_by_phone(user_id, formatted_phone)
                if existing:
                    errors.append(f"Row {row_num}: contact with phone {formatted_phone} already exists")
                    continue
                
                contact_data = {
                    'user_id': user_id,
                    'name': name,
                    'phone_number': formatted_phone,
                    'email': row.get('email', '').strip(),
                    'company': row.get('company', '').strip(),
                    'notes': row.get('notes', '').strip(),
                    'is_blocked': False,
                    'is_favorite': False,
                    'tags': []
                }
                
                # Validate email if provided
                if contact_data['email']:
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, contact_data['email']):
                        errors.append(f"Row {row_num}: invalid email format")
                        continue
                
                repo.create_contact(contact_data)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        logger.info(f"Imported {imported_count} contacts for user {user_id}")
        
        return jsonify({
            "imported_count": imported_count,
            "errors": errors[:10]  # Limit errors shown
        })
        
    except Exception as e:
        logger.error(f"Error importing contacts: {e}")
        return jsonify({"error": "failed to import contacts"}), 500

@bp.post("/export")
def export_contacts():
    """Export contacts to CSV format"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        # Get all contacts for export
        contacts = repo.list_contacts(user_id, 1, 10000, '', 'name')  # Large limit for export
        
        # Generate CSV data
        import csv
        import io
        from datetime import datetime
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # CSV headers
        writer.writerow([
            'Name', 'Phone Number', 'Email', 'Company', 'Notes', 
            'Is Blocked', 'Is Favorite', 'Created At'
        ])
        
        # CSV data
        for contact in contacts:
            writer.writerow([
                contact.get('name'),
                contact.get('phone_number'),
                contact.get('email', ''),
                contact.get('company', ''),
                contact.get('notes', ''),
                contact.get('is_blocked', False),
                contact.get('is_favorite', False),
                contact.get('created_at')
            ])
        
        csv_data = output.getvalue()
        output.close()
        
        return jsonify({
            "csv_data": csv_data,
            "filename": f"contacts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "total_records": len(contacts)
        })
        
    except Exception as e:
        logger.error(f"Error exporting contacts: {e}")
        return jsonify({"error": "failed to export contacts"}), 500

@bp.get("/<int:contact_id>/call-history")
def get_contact_call_history(contact_id):
    """Get call history for a specific contact"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        contacts_repo = ContactsRepository(cfg.database_url, cfg.queries)
        
        # Verify contact exists and belongs to user
        contact = contacts_repo.get_contact(contact_id, user_id)
        if not contact:
            return jsonify({"error": "contact not found"}), 404
        
        # Get call history for this contact's phone number
        from api.repositories.calls_repo import CallsRepository
        calls_repo = CallsRepository(cfg.database_url, cfg.queries)
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        
        calls = calls_repo.get_calls_by_phone(user_id, contact['phone_number'], page, limit)
        total = calls_repo.count_calls_by_phone(user_id, contact['phone_number'])
        
        return jsonify({
            "contact": contact,
            "calls": calls,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting call history for contact {contact_id}: {e}")
        return jsonify({"error": "failed to retrieve call history"}), 500   


from flask import Blueprint, current_app, request, jsonify
from api.repositories.feed_repo import FeedRepository
from api.utils.validation import contains_sensitive
from api.controllers.texts_controller import require_auth  
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

bp = Blueprint("feed", __name__)

@bp.post("")
def create_feed():
    cfg = current_app.config["APP_CONFIG"]
    repo = FeedRepository(cfg.database_url, cfg.queries)
    payload = request.get_json(force=True)
    text = f"{payload.get('title','')}\n{payload.get('body','')}"
    if contains_sensitive(text, cfg.policies.get("sensitive_blocklist", [])):
        return jsonify({"error": "Sensitive data detected. Please remove or confirm via safe channel."}), 400
    item = repo.create(user_id=1, title=payload["title"], body=payload["body"], tags=payload.get("tags", []))
    if not item:
        return jsonify({"error": "Create failed"}), 500
    return jsonify({"id": item[0]}), 201

@bp.get("/active")
def list_active():
    cfg = current_app.config["APP_CONFIG"]
    repo = FeedRepository(cfg.database_url, cfg.queries)
    rows = repo.list_active(user_id=1)
    return jsonify(rows or [])

@bp.get("/tags")
def get_tags():
    """Get all tags used by the user"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = FeedRepository(cfg.database_url, cfg.queries)
        
        tags = repo.get_user_tags(user_id)
        return jsonify({"tags": tags or []})
        
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return jsonify({"error": "failed to retrieve tags"}), 500

@bp.post("/bulk-action")
def bulk_action():
    """Perform bulk actions on multiple feed items"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "invalid JSON data"}), 400
        
        item_ids = payload.get('item_ids', [])
        action = payload.get('action')  # 'archive', 'restore', 'delete', 'add_tag', 'remove_tag'
        
        if not item_ids or not action:
            return jsonify({"error": "item_ids and action are required"}), 400
        
        if not isinstance(item_ids, list) or len(item_ids) > 100:
            return jsonify({"error": "item_ids must be a list with max 100 items"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = FeedRepository(cfg.database_url, cfg.queries)
        
        results = {"success": 0, "failed": 0, "errors": []}
        
        for item_id in item_ids:
            try:
                # Verify item belongs to user
                item = repo.get_feed_item(item_id, user_id)
                if not item:
                    results["failed"] += 1
                    results["errors"].append(f"Item {item_id} not found")
                    continue
                
                success = False
                if action == 'archive':
                    success = repo.update_feed_item(item_id, {'is_active': False})
                elif action == 'restore':
                    success = repo.update_feed_item(item_id, {'is_active': True})
                elif action == 'delete':
                    success = repo.delete_feed_item(item_id, user_id)
                elif action == 'add_tag':
                    tag = payload.get('tag')
                    if tag:
                        current_tags = item.get('tags', [])
                        if tag not in current_tags:
                            current_tags.append(tag)
                            success = repo.update_feed_item(item_id, {'tags': current_tags})
                elif action == 'remove_tag':
                    tag = payload.get('tag')
                    if tag:
                        current_tags = item.get('tags', [])
                        if tag in current_tags:
                            current_tags.remove(tag)
                            success = repo.update_feed_item(item_id, {'tags': current_tags})
                
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Action failed for item {item_id}")
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error processing item {item_id}: {str(e)}")
        
        logger.info(f"Bulk action '{action}' completed: {results['success']} success, {results['failed']} failed")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error performing bulk action: {e}")
        return jsonify({"error": "failed to perform bulk action"}), 500

@bp.get("/search")
def search_feed():
    """Search feed items by content"""
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
        repo = FeedRepository(cfg.database_url, cfg.queries)
        
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        
        results = repo.search_feed_items(user_id, query, page, limit)
        total = repo.count_search_results(user_id, query)
        
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
        logger.error(f"Error searching feed items: {e}")
        return jsonify({"error": "failed to search feed items"}), 500

@bp.post("/import")
def import_feed():
    """Import feed items from external sources"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "invalid JSON data"}), 400
        
        items = payload.get('items', [])
        source = payload.get('source', 'manual')
        
        if not items or not isinstance(items, list):
            return jsonify({"error": "items array is required"}), 400
        
        if len(items) > 50:
            return jsonify({"error": "maximum 50 items per import"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = FeedRepository(cfg.database_url, cfg.queries)
        
        results = {"imported": 0, "skipped": 0, "errors": []}
        
        for item_data in items:
            try:
                title = item_data.get('title', '').strip()
                body = item_data.get('body', '').strip()
                tags = item_data.get('tags', [])
                
                if not title or not body:
                    results["skipped"] += 1
                    results["errors"].append("Item missing title or body")
                    continue
                
                # Check for sensitive content
                text = f"{title}\n{body}"
                if contains_sensitive(text, cfg.policies.get("sensitive_blocklist", [])):
                    results["skipped"] += 1
                    results["errors"].append(f"Sensitive content detected in: {title[:50]}...")
                    continue
                
                # Add import source tag
                if source not in tags:
                    tags.append(f"imported-{source}")
                
                item = repo.create(user_id=user_id, title=title, body=body, tags=tags)
                if item:
                    results["imported"] += 1
                else:
                    results["skipped"] += 1
                    results["errors"].append(f"Failed to create item: {title[:50]}...")
                    
            except Exception as e:
                results["skipped"] += 1
                results["errors"].append(f"Error processing item: {str(e)}")
        
        logger.info(f"Import completed: {results['imported']} imported, {results['skipped']} skipped")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error importing feed items: {e}")
        return jsonify({"error": "failed to import feed items"}), 500

@bp.get("/export")
def export_feed():
    """Export feed items to various formats"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        format_type = request.args.get('format', 'json').lower()
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        tag_filter = request.args.get('tag')
        
        if format_type not in ['json', 'csv', 'txt']:
            return jsonify({"error": "supported formats: json, csv, txt"}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = FeedRepository(cfg.database_url, cfg.queries)
        
        # Get all items for export
        items = repo.export_feed_items(user_id, include_archived, tag_filter)
        
        if format_type == 'json':
            return jsonify({
                "export_date": datetime.now().isoformat(),
                "user_id": user_id,
                "total_items": len(items),
                "include_archived": include_archived,
                "tag_filter": tag_filter,
                "items": items
            })
        
        elif format_type == 'csv':
            # For CSV, you'd typically use Flask's make_response with proper headers
            # This is a simplified JSON response showing the structure
            csv_data = []
            for item in items:
                csv_data.append({
                    "id": item.get('id'),
                    "title": item.get('title'),
                    "body": item.get('body'),
                    "tags": ','.join(item.get('tags', [])),
                    "is_active": item.get('is_active'),
                    "created_at": item.get('created_at'),
                    "updated_at": item.get('updated_at')
                })
            
            return jsonify({
                "format": "csv",
                "data": csv_data,
                "note": "In production, this would return actual CSV content"
            })
        
        elif format_type == 'txt':
            text_content = f"Feed Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            text_content += f"Total Items: {len(items)}\n"
            text_content += "=" * 50 + "\n\n"
            
            for item in items:
                text_content += f"Title: {item.get('title')}\n"
                text_content += f"Tags: {', '.join(item.get('tags', []))}\n"
                text_content += f"Created: {item.get('created_at')}\n"
                text_content += f"Content:\n{item.get('body')}\n"
                text_content += "-" * 30 + "\n\n"
            
            return jsonify({
                "format": "txt",
                "content": text_content,
                "note": "In production, this would return actual text file"
            })
        
    except Exception as e:
        logger.error(f"Error exporting feed items: {e}")
        return jsonify({"error": "failed to export feed items"}), 500

@bp.get("/stats")
def get_feed_stats():
    """Get statistics about user's feed items"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = FeedRepository(cfg.database_url, cfg.queries)
        
        stats = repo.get_feed_statistics(user_id)
        
        return jsonify({
            "total_items": stats.get('total_items', 0),
            "active_items": stats.get('active_items', 0),
            "archived_items": stats.get('archived_items', 0),
            "tags_count": stats.get('tags_count', 0),
            "last_updated": stats.get('last_updated')
        })
        
    except Exception as e:
        logger.error(f"Error getting feed stats: {e}")
        return jsonify({"error": "failed to retrieve feed statistics"}), 500

@bp.put("/<int:item_id>")
def update_feed_item(item_id):
    """Update a specific feed item"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "invalid JSON data"}), 400
        
        # Verify item belongs to user
        cfg = current_app.config["APP_CONFIG"]
        repo = FeedRepository(cfg.database_url, cfg.queries)
        item = repo.get_feed_item(item_id, user_id)
        if not item:
            return jsonify({"error": "feed item not found"}), 404
        
        # Validate and sanitize input
        update_data = {}
        if 'title' in payload:
            title = payload['title'].strip()
            if not title:
                return jsonify({"error": "title cannot be empty"}), 400
            update_data['title'] = title
        
        if 'body' in payload:
            body = payload['body'].strip()
            if not body:
                return jsonify({"error": "body cannot be empty"}), 400
            update_data['body'] = body
            
        if 'tags' in payload:
            if not isinstance(payload['tags'], list):
                return jsonify({"error": "tags must be an array"}), 400
            update_data['tags'] = payload['tags']
            
        if 'is_active' in payload:
            if not isinstance(payload['is_active'], bool):
                return jsonify({"error": "is_active must be a boolean"}), 400
            update_data['is_active'] = payload['is_active']
        
        # Check for sensitive content if title or body is being updated
        if update_data.get('title') or update_data.get('body'):
            text = f"{update_data.get('title', item.get('title', ''))}\n{update_data.get('body', item.get('body', ''))}"
            if contains_sensitive(text, cfg.policies.get("sensitive_blocklist", [])):
                return jsonify({"error": "Sensitive data detected. Please remove or confirm via safe channel."}), 400
        
        # Perform update
        success = repo.update_feed_item(item_id, update_data)
        if not success:
            return jsonify({"error": "update failed"}), 500
        
        # Return updated item
        updated_item = repo.get_feed_item(item_id, user_id)
        return jsonify(updated_item)
        
    except Exception as e:
        logger.error(f"Error updating feed item {item_id}: {e}")
        return jsonify({"error": "failed to update feed item"}), 500

@bp.delete("/<int:item_id>")
def delete_feed_item(item_id):
    """Delete a specific feed item"""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401
    
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = FeedRepository(cfg.database_url, cfg.queries)
        
        # Verify item belongs to user
        item = repo.get_feed_item(item_id, user_id)
        if not item:
            return jsonify({"error": "feed item not found"}), 404
        
        # Delete the item
        success = repo.delete_feed_item(item_id, user_id)
        if not success:
            return jsonify({"error": "delete failed"}), 500
        
        return jsonify({"message": "feed item deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting feed item {item_id}: {e}")
        return jsonify({"error": "failed to delete feed item"}), 500


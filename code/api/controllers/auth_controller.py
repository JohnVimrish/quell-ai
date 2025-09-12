
from flask import Blueprint, current_app, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from api.repositories.users_repo import UsersRepository
import re
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def handle_auth_errors(f):
    """Decorator for handling authentication errors"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication error in {f.__name__}: {str(e)}")
            return jsonify({"error": "An internal error occurred"}), 500
    return decorated_function

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function


def validate_email(email):
    """Validate email format"""
    # Fix the missing quote
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Additional validation checks
    if not email or len(email) > 254:  # RFC 5321 limit
        return False
    
    # Check for consecutive dots
    if '..' in email:
        return False
    
    # Check for leading/trailing dots in local part
    local_part = email.split('@')[0] if '@' in email else email
    if local_part.startswith('.') or local_part.endswith('.'):
        return False
    
    # Basic regex check
    if not re.match(pattern, email):
        return False
    
    # Additional domain validation
    if '@' in email:
        local, domain = email.rsplit('@', 1)
        
        # Local part length check (RFC 5321)
        if len(local) > 64:
            return False
        
        # Domain part checks
        if len(domain) > 253:
            return False
        
        # Domain must have at least one dot
        if '.' not in domain:
            return False
        
        # Domain parts shouldn't start or end with hyphens
        domain_parts = domain.split('.')
        for part in domain_parts:
            if part.startswith('-') or part.endswith('-') or len(part) == 0:
                return False
    
    return True

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@bp.post("/register")
@handle_auth_errors
def register():
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = UsersRepository(cfg.database_url, cfg.queries)
        data = request.get_json(force=True)
        
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
            
        email = data.get("email","").strip().lower()
        password = data.get("password","")
        
        if not email or not password:
            return jsonify({"error":"email and password required"}), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({"error":"invalid email format"}), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Check if user already exists
        existing_user = repo.get_by_email(email)
        if existing_user:
            return jsonify({"error":"email already registered"}), 409
        
        user = repo.create(email, generate_password_hash(password))
        if not user:
            return jsonify({"error": "failed to create user"}), 500
            
        session["user_id"] = user[0]
        logger.info(f"User registered successfully: {email}")
        return jsonify({"id": user[0], "email": email}), 201
        
    except ValueError as e:
        logger.warning(f"Invalid registration data: {str(e)}")
        return jsonify({"error": "invalid data provided"}), 400
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "registration failed"}), 500

@bp.post("/login")
@handle_auth_errors
def login():
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = UsersRepository(cfg.database_url, cfg.queries)
        data = request.get_json(force=True)
        
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
            
        email = data.get("email","").strip().lower()
        password = data.get("password","")
        
        if not email or not password:
            return jsonify({"error":"email and password required"}), 400
        
        u = repo.get_by_email(email)
        if not u:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return jsonify({"error":"invalid credentials"}), 401
            
        if not check_password_hash(u[2], password):
            logger.warning(f"Failed login attempt for email: {email}")
            return jsonify({"error":"invalid credentials"}), 401
        
        session["user_id"] = u[0]
        logger.info(f"User logged in successfully: {email}")
        return jsonify({"id": u[0], "email": email})
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "login failed"}), 500

@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})

@bp.get("/me")
@require_auth
@handle_auth_errors
def get_current_user():
    """Get current authenticated user info"""
    try:
        user_id = session.get("user_id")
        cfg = current_app.config["APP_CONFIG"]
        repo = UsersRepository(cfg.database_url, cfg.queries)
        user = repo.get_by_id(user_id)
        
        if not user:
            session.clear()  # Clear invalid session
            logger.warning(f"User not found for session user_id: {user_id}")
            return jsonify({"error": "user not found"}), 404
        
        return jsonify({"id": user[0], "email": user[1]})
        
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify({"error": "failed to get user info"}), 500

@bp.post("/change-password")
@require_auth
@handle_auth_errors
def change_password():
    """Change user password"""
    try:
        user_id = session.get("user_id")
        data = request.get_json(force=True)
        
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
            
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        
        if not current_password or not new_password:
            return jsonify({"error": "current and new password required"}), 400
        
        # Validate new password strength
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = UsersRepository(cfg.database_url, cfg.queries)
        user = repo.get_by_id(user_id)
        
        if not user:
            session.clear()
            return jsonify({"error": "user not found"}), 404
            
        if not check_password_hash(user[2], current_password):
            logger.warning(f"Invalid current password for user: {user_id}")
            return jsonify({"error": "invalid current password"}), 401
        
        # Update password
        success = repo.update_password(user_id, generate_password_hash(new_password))
        if not success:
            return jsonify({"error": "failed to update password"}), 500
        
        logger.info(f"Password changed successfully for user: {user_id}")
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({"error": "failed to change password"}), 500

    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@bp.post("/register")
@handle_auth_errors
def register():
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = UsersRepository(cfg.database_url, cfg.queries)
        data = request.get_json(force=True)
        
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
            
        email = data.get("email","").strip().lower()
        password = data.get("password","")
        
        if not email or not password:
            return jsonify({"error":"email and password required"}), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({"error":"invalid email format"}), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Check if user already exists
        existing_user = repo.get_by_email(email)
        if existing_user:
            return jsonify({"error":"email already registered"}), 409
        
        user = repo.create(email, generate_password_hash(password))
        if not user:
            return jsonify({"error": "failed to create user"}), 500
            
        session["user_id"] = user[0]
        logger.info(f"User registered successfully: {email}")
        return jsonify({"id": user[0], "email": email}), 201
        
    except ValueError as e:
        logger.warning(f"Invalid registration data: {str(e)}")
        return jsonify({"error": "invalid data provided"}), 400
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "registration failed"}), 500

@bp.post("/login")
@handle_auth_errors
def login():
    try:
        cfg = current_app.config["APP_CONFIG"]
        repo = UsersRepository(cfg.database_url, cfg.queries)
        data = request.get_json(force=True)
        
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
            
        email = data.get("email","").strip().lower()
        password = data.get("password","")
        
        if not email or not password:
            return jsonify({"error":"email and password required"}), 400
        
        u = repo.get_by_email(email)
        if not u:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return jsonify({"error":"invalid credentials"}), 401
            
        if not check_password_hash(u[2], password):
            logger.warning(f"Failed login attempt for email: {email}")
            return jsonify({"error":"invalid credentials"}), 401
        
        session["user_id"] = u[0]
        logger.info(f"User logged in successfully: {email}")
        return jsonify({"id": u[0], "email": email})
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "login failed"}), 500

@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})

@bp.get("/me")
@require_auth
@handle_auth_errors
def get_current_user():
    """Get current authenticated user info"""
    try:
        user_id = session.get("user_id")
        cfg = current_app.config["APP_CONFIG"]
        repo = UsersRepository(cfg.database_url, cfg.queries)
        user = repo.get_by_id(user_id)
        
        if not user:
            session.clear()  # Clear invalid session
            logger.warning(f"User not found for session user_id: {user_id}")
            return jsonify({"error": "user not found"}), 404
        
        return jsonify({"id": user[0], "email": user[1]})
        
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify({"error": "failed to get user info"}), 500

@bp.post("/change-password")
@require_auth
@handle_auth_errors
def change_password():
    """Change user password"""
    try:
        user_id = session.get("user_id")
        data = request.get_json(force=True)
        
        if not data:
            return jsonify({"error": "invalid JSON data"}), 400
            
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        
        if not current_password or not new_password:
            return jsonify({"error": "current and new password required"}), 400
        
        # Validate new password strength
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        cfg = current_app.config["APP_CONFIG"]
        repo = UsersRepository(cfg.database_url, cfg.queries)
        user = repo.get_by_id(user_id)
        
        if not user:
            session.clear()
            return jsonify({"error": "user not found"}), 404
            
        if not check_password_hash(user[2], current_password):
            logger.warning(f"Invalid current password for user: {user_id}")
            return jsonify({"error": "invalid current password"}), 401
        
        # Update password
        success = repo.update_password(user_id, generate_password_hash(new_password))
        if not success:
            return jsonify({"error": "failed to update password"}), 500
        
        logger.info(f"Password changed successfully for user: {user_id}")
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({"error": "failed to change password"}), 500

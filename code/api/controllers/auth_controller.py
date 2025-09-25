
from flask import Blueprint, current_app, request, jsonify, session, render_template, redirect, url_for, flash
from functools import wraps
import re
import logging
from api.utils.security import PasswordManager
from api.repositories.users_repo import UsersRepository

logger = logging.getLogger(__name__)

# Create the blueprint
bp = Blueprint("auth", __name__)

def handle_auth_errors(f):
    """Decorator to handle authentication errors"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Auth error in {f.__name__}: {e}")
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication failed", "details": str(e)}), 500
            else:
                flash("Authentication error occurred", "error")
                return redirect(url_for('auth.login'))
    return decorated_function

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            if request.path.startswith('/api/'):
                return jsonify({"error": "authentication required"}), 401
            else:
                flash("Please log in to access this page", "info")
                return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.match(pattern, email) is not None

def get_user_repository():
    """Get user repository instance"""
    return UsersRepository()

# Web Routes (for rendering templates)
@bp.route("/login")
def login_page():
    """Login page"""
    if session.get("user_id"):
        return redirect(url_for('dashboard'))
    return render_template("auth/login.html")

@bp.route("/register")
def register_page():
    """Registration page"""
    if session.get("user_id"):
        return redirect(url_for('dashboard'))
    return render_template("auth/register.html")

# API Routes (for AJAX/API calls)
@bp.post("/register")
@handle_auth_errors
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip() or None
        
        # Validation
        if not email or not password or not name:
            return jsonify({"error": "Email, password, and name are required"}), 400
        
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Validate password strength
        is_valid, message = PasswordManager.validate_password_strength(password)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Get user repository
        user_repo = get_user_repository()
        
        # Check if user already exists
        if user_repo.check_email_exists(email):
            return jsonify({"error": "Email already registered"}), 409
        
        # Check phone if provided
        if phone and user_repo.check_phone_exists(phone):
            return jsonify({"error": "Phone number already registered"}), 409
        
        # Hash password
        password_hash = PasswordManager.hash_password(password)
        
        # Create user in database
        user_data = user_repo.create_user(email, password_hash, phone)
        if not user_data:
            return jsonify({"error": "Failed to create user account"}), 500
        
        user_id = user_data['id']
        
        # Create default user settings
        try:
            user_repo.create_user_settings(user_id)
        except Exception as e:
            logger.warning(f"Failed to create user settings: {e}")
            # Continue without settings - they can be created later
        
        # Create session
        session["user_id"] = user_id
        session["user_email"] = email
        session["user_name"] = name
        session.permanent = True
        
        logger.info(f"User registered successfully: {email} (ID: {user_id})")
        
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user": {
                "id": user_id,
                "email": email,
                "name": name
            },
            "redirect_url": "/dashboard"
        })
        
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return jsonify({"error": "Registration failed. Please try again."}), 500

@bp.post("/login")
@handle_auth_errors
def login():
    """Login user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Get user repository
        user_repo = get_user_repository()
        
        # Get user from database
        user_data = user_repo.get_user_by_email_for_login(email)
        if not user_data:
            logger.warning(f"Login attempt with non-existent email: {email}")
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Verify password
        if not PasswordManager.verify_password(password, user_data['password_hash']):
            logger.warning(f"Login attempt with invalid password for: {email}")
            return jsonify({"error": "Invalid credentials"}), 401
        
        user_id = user_data['id']
        
        # Update last login timestamp
        user_repo.update_last_login(user_id)
        
        # Get user settings
        user_settings = user_repo.get_user_settings(user_id)
        
        # Create session
        session["user_id"] = user_id
        session["user_email"] = email
        session["user_name"] = email.split('@')[0].title()
        session.permanent = True
        
        # Initialize AI mode settings from database or defaults
        session['ai_mode_settings'] = {
            'active': user_settings.get('ai_mode_enabled', False) if user_settings else False,
            'auto_disable_time': user_settings.get('ai_mode_expires_at') if user_settings else None,
            'voice_model_id': None,  # Will be set when voice model is trained
            'spam_sensitivity': current_app.config.get("SPAM_SENSITIVITY_DEFAULT", "medium"),
            'recording_enabled': user_settings.get('recording_enabled', False) if user_settings else False
        }
        
        logger.info(f"User logged in successfully: {email} (ID: {user_id})")
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user_id,
                "email": email,
                "name": session["user_name"]
            },
            "redirect_url": "/dashboard"
        })
            
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return jsonify({"error": "Login failed. Please try again."}), 500

@bp.post("/logout")
def logout():
    """Logout user"""
    user_email = session.get("user_email")
    session.clear()
    
    if user_email:
        logger.info(f"User logged out: {user_email}")
    
    return jsonify({"success": True, "message": "Logged out successfully"})

@bp.get("/me")
@require_auth
@handle_auth_errors
def get_current_user():
    """Get current user information"""
    try:
        user_data = {
            "id": session.get("user_id"),
            "email": session.get("user_email"),
            "name": session.get("user_name"),
            "ai_mode_settings": session.get("ai_mode_settings", {})
        }
        
        return jsonify({
            "success": True,
            "user": user_data
        })
        
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        return jsonify({"error": "Failed to get user info"}), 500

@bp.post("/change-password")
@require_auth
@handle_auth_errors
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({"error": "Current and new passwords are required"}), 400
        
        # Validate new password strength
        is_valid, message = PasswordManager.validate_password_strength(new_password)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Get user repository
        user_repo = get_user_repository()
        user_id = session.get("user_id")
        
        # Get current user data
        user_data = user_repo.get_user_by_id(user_id)
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
        # Verify current password
        if not PasswordManager.verify_password(current_password, user_data['password_hash']):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Hash new password
        new_password_hash = PasswordManager.hash_password(new_password)
        
        # Update password in database
        if not user_repo.update_password(user_id, new_password_hash):
            return jsonify({"error": "Failed to update password"}), 500
        
        logger.info(f"Password changed successfully for user: {session.get('user_email')}")
        
        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        })
        
    except Exception as e:
        logger.error(f"Failed to change password: {e}")
        return jsonify({"error": "Failed to change password"}), 500

# Helper route for checking auth status
@bp.get("/status")
def auth_status():
    """Check authentication status"""
    user_id = session.get("user_id")
    return jsonify({
        "authenticated": bool(user_id),
        "user_id": user_id,
        "user_email": session.get("user_email"),
        "user_name": session.get("user_name")
    })


from flask import Blueprint, current_app, request, jsonify, session, render_template, redirect, url_for, flash
from functools import wraps
import re
import logging
import hashlib
import secrets

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

def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(password, hashed_password):
    """Verify password against hash"""
    try:
        salt, password_hash = hashed_password.split(':')
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == password_hash
    except:
        return False

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
        
        # Validation
        if not email or not password or not name:
            return jsonify({"error": "Email, password, and name are required"}), 400
        
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Check if user already exists (simplified - you'd check database)
        # For now, we'll just create a session
        user_id = f"user_{hash(email)}"
        
        # In a real app, you'd save to database here
        # user_repo.create_user(email, hash_password(password), name)
        
        # Create session
        session["user_id"] = user_id
        session["user_email"] = email
        session["user_name"] = name
        session.permanent = True
        
        logger.info(f"User registered: {email}")
        
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user": {
                "id": user_id,
                "email": email,
                "name": name
            }
        })
        
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return jsonify({"error": "Registration failed"}), 500

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
        
        # In a real app, you'd verify against database
        # For demo purposes, accept any valid email/password combo
        if len(password) >= 6:  # Simple validation for demo
            user_id = f"user_{hash(email)}"
            
            # Create session
            session["user_id"] = user_id
            session["user_email"] = email
            session["user_name"] = email.split('@')[0].title()
            session.permanent = True
            
            # Initialize AI mode settings
            session['ai_mode_settings'] = {
                'active': False,
                'auto_disable_time': None,
                'voice_model_id': None,
                'spam_sensitivity': current_app.config.get("SPAM_SENSITIVITY_DEFAULT", "medium"),
                'recording_enabled': current_app.config.get("CALL_RECORDING_ENABLED", False)
            }
            
            logger.info(f"User logged in: {email}")
            
            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": session["user_name"]
                }
            })
        else:
            return jsonify({"error": "Invalid credentials"}), 401
            
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return jsonify({"error": "Login failed"}), 500

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
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # In a real app, you'd verify current password and update in database
        # For demo, just return success
        
        logger.info(f"Password changed for user: {session.get('user_email')}")
        
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

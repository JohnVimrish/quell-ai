import os
import logging
import asyncio
from datetime import datetime, timedelta
from flask import Flask, session, g, render_template, redirect, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from api.utils.config import Config
from api.utils.logging import LoggerManager
from api.db.connection import DatabaseManager
from api.models.spam_detector import AdvancedSpamDetector as SpamDetector
from api.models.rag_system import RAGSystem
from api.models.voice_model import VoiceModel
from api.controllers import (
    feed_controller,
    copilot_controller,
    contacts_controller,
    calls_controller,
    texts_controller,
    report_controller,
    webhooks_controller,
    auth_controller,
)

def create_app(config_override=None):
    """Create and configure the Flask application"""
        # Get the correct paths
    current_dir = os.path.dirname(os.path.abspath(__file__))  # api/
    project_root = os.path.dirname(current_dir)  # code/
    template_dir = os.path.join(project_root, 'ui', 'templates')
    static_dir = os.path.join(project_root, 'ui', 'static')
    
    print(f"Template dir: {template_dir}")  # Debug
    print(f"Static dir: {static_dir}")      # Debug
    print(f"Template dir exists: {os.path.exists(template_dir)}")
    print(f"Static dir exists: {os.path.exists(static_dir)}")
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir,
                static_url_path='/static')
    
    # Initialize SocketIO for real-time features
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Load configuration
    try:
        cfg = config_override or Config.load()
        app.config["APP_CONFIG"] = cfg
        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
        app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB for voice uploads
        
        # AI Configuration
        app.config["AI_MODEL_PATH"] = os.getenv("AI_MODEL_PATH", "models/")
        app.config["VOICE_SAMPLES_PATH"] = os.getenv("VOICE_SAMPLES_PATH", "voice_samples/")
        app.config["TRANSCRIPTS_PATH"] = os.getenv("TRANSCRIPTS_PATH", "transcripts/")
        
        # External API Keys
        app.config["TWILIO_ACCOUNT_SID"] = os.getenv("TWILIO_ACCOUNT_SID")
        app.config["TWILIO_AUTH_TOKEN"] = os.getenv("TWILIO_AUTH_TOKEN")
        app.config["DEEPGRAM_API_KEY"] = os.getenv("DEEPGRAM_API_KEY")
        app.config["ELEVENLABS_API_KEY"] = os.getenv("ELEVENLABS_API_KEY")
        app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        
        # Database configuration
        app.config["DATABASE_URL"] = os.getenv("DATABASE_URL")
        app.config["DEBUG"] = cfg.debug
        
        # Feed configuration (7-day active, 7-day archive)
        app.config["FEED_ACTIVE_DAYS"] = int(os.getenv("FEED_ACTIVE_DAYS", 7))
        app.config["FEED_ARCHIVE_DAYS"] = int(os.getenv("FEED_ARCHIVE_DAYS", 7))
        
        # AI Mode configuration
        app.config["AI_MODE_MAX_DURATION"] = int(os.getenv("AI_MODE_MAX_DURATION", 480))  # 8 hours
        app.config["AI_DISCLOSURE_REQUIRED"] = os.getenv("AI_DISCLOSURE_REQUIRED", "true").lower() == "true"
        
        # Voice cloning configuration
        app.config["VOICE_CLONING_ENABLED"] = os.getenv("VOICE_CLONING_ENABLED", "true").lower() == "true"
        app.config["VOICE_DISCLOSURE_REQUIRED"] = os.getenv("VOICE_DISCLOSURE_REQUIRED", "true").lower() == "true"
        
        # Spam detection configuration
        app.config["SPAM_DETECTION_ENABLED"] = os.getenv("SPAM_DETECTION_ENABLED", "true").lower() == "true"
        app.config["SPAM_SENSITIVITY_DEFAULT"] = os.getenv("SPAM_SENSITIVITY_DEFAULT", "medium")
        
        # Call recording configuration
        app.config["CALL_RECORDING_ENABLED"] = os.getenv("CALL_RECORDING_ENABLED", "false").lower() == "true"
        app.config["RECORDING_CONSENT_REQUIRED"] = os.getenv("RECORDING_CONSENT_REQUIRED", "true").lower() == "true"
        
    except Exception as e:
        print(f"Error loading configuration: {e}")
        raise
    
    # Initialize logging
    try:
        logger_manager = LoggerManager()  # No arguments
        logger_manager.configure(cfg.logging)  # Configure separately
        logger = logging.getLogger(__name__)
        logger.info("Application starting up")
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
    
    # Enable CORS
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ])
    
    # Initialize database
    try:
        db_manager = DatabaseManager(cfg.database_url)
        app.config["DB_MANAGER"] = db_manager
        
        with app.app_context():
            db_manager.test_connection()
            logger.info("Database connection established")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        app.config["DB_MANAGER"] = None
    
    # Initialize AI Models
# Around line 105-130, replace the AI Models initialization section:

    # Initialize AI Models
    try:
        # Initialize spam detector
        if app.config["SPAM_DETECTION_ENABLED"]:
            spam_detector = SpamDetector(cfg)  # Pass config here
            app.config["SPAM_DETECTOR"] = spam_detector
            logger.info("Spam detector initialized")
        else:
            app.config["SPAM_DETECTOR"] = None
            logger.info("Spam detection disabled by configuration")
        
        # Initialize RAG system for AI instructions
        rag_system = RAGSystem(cfg)
        app.config["RAG_SYSTEM"] = rag_system
        
        # Initialize voice model if voice cloning is enabled
        if app.config["VOICE_CLONING_ENABLED"]:
            voice_model = VoiceModel()
            app.config["VOICE_MODEL"] = voice_model
            logger.info("Voice model initialized")
        else:
            app.config["VOICE_MODEL"] = None
            logger.info("Voice cloning disabled by configuration")
        
        logger.info("AI models initialized")
        
    except Exception as e:
        logger.error(f"AI model initialization failed: {e}")
        app.config["SPAM_DETECTOR"] = None
        app.config["RAG_SYSTEM"] = None
        app.config["VOICE_MODEL"] = None
    
    # Create necessary directories
    os.makedirs(app.config["AI_MODEL_PATH"], exist_ok=True)
    os.makedirs(app.config["VOICE_SAMPLES_PATH"], exist_ok=True)
    os.makedirs(app.config["TRANSCRIPTS_PATH"], exist_ok=True)
    
    # Request context processors
    @app.before_request
    def before_request():
        """Set up request context"""
        g.config = app.config["APP_CONFIG"]
        g.db_manager = app.config.get("DB_MANAGER")
        g.spam_detector = app.config.get("SPAM_DETECTOR")
        g.rag_system = app.config.get("RAG_SYSTEM")
        g.voice_model = app.config.get("VOICE_MODEL")
        
        # Make session permanent
        session.permanent = True
        
        # Initialize user session data if not exists
        if 'user_id' in session and 'ai_mode_settings' not in session:
            session['ai_mode_settings'] = {
                'active': False,
                'auto_disable_time': None,
                'voice_model_id': None,
                'spam_sensitivity': app.config.get("SPAM_SENSITIVITY_DEFAULT", "medium"),
                'recording_enabled': app.config.get("CALL_RECORDING_ENABLED", False)
            }
    
    @app.after_request
    def after_request(response):
        """Clean up after request"""
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Add CORS headers for API endpoints
        if request.path.startswith('/api/'):
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    @app.teardown_appcontext
    def close_db(error):
        """Close database connections"""
        if hasattr(g, 'db_connection'):
            g.db_connection.close()
    
    # Enhanced error handlers
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 error: {request.url}")
        if request.path.startswith('/api/'):
            return jsonify({"error": "Resource not found", "code": 404}), 404
        return render_template("errors/404.html"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({"error": "Internal server error", "code": 500}), 500
        return render_template("errors/500.html"), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        logger.warning(f"File too large: {request.url}")
        return jsonify({"error": "File too large. Maximum size is 50MB", "code": 413}), 413
    
    # Enhanced health check
    @app.route("/healthz")
    def health_check():
        """Comprehensive health check endpoint"""
        try:
            health_status = {
                "status": "healthy",
                "service": "communicator-copilot",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {}
            }
            
            # Check database
            try:
                if g.db_manager:
                    g.db_manager.test_connection()
                    health_status["components"]["database"] = "healthy"
                else:
                    health_status["components"]["database"] = "not_configured"
            except Exception as e:
                health_status["components"]["database"] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"
            
            # Check AI models
            try:
                if g.spam_detector:
                    health_status["components"]["spam_detector"] = "healthy"
                else:
                    health_status["components"]["spam_detector"] = "not_loaded"
                
                if g.rag_system:
                    health_status["components"]["rag_system"] = "healthy"
                else:
                    health_status["components"]["rag_system"] = "not_loaded"
                    
                if g.voice_model:
                    health_status["components"]["voice_model"] = "healthy"
                else:
                    health_status["components"]["voice_model"] = "not_loaded"
            except Exception as e:
                health_status["components"]["ai_models"] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"
            
            # Check external services
            external_services = {
                "twilio": bool(app.config.get("TWILIO_ACCOUNT_SID")),
                "deepgram": bool(app.config.get("DEEPGRAM_API_KEY")),
                "elevenlabs": bool(app.config.get("ELEVENLABS_API_KEY")),
                "openai": bool(app.config.get("OPENAI_API_KEY"))
            }
            health_status["components"]["external_services"] = external_services
            
            status_code = 200 if health_status["status"] == "healthy" else 503
            return jsonify(health_status), status_code
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 503
    
    # AI Mode management with timed sessions
    @app.route("/api/ai-mode/toggle", methods=["POST"])
    def toggle_ai_mode():
        """Toggle AI mode with optional duration"""
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        try:
            data = request.get_json() or {}
            duration_minutes = data.get("duration_minutes")
            
            current_settings = session.get("ai_mode_settings", {})
            current_state = current_settings.get("active", False)
            new_state = not current_state
            
            # Update settings
            current_settings["active"] = new_state
            
            if new_state and duration_minutes:
                # Validate duration against max allowed
                max_duration = app.config.get("AI_MODE_MAX_DURATION", 480)
                duration_minutes = min(duration_minutes, max_duration)
                
                # Set auto-disable time
                auto_disable_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
                current_settings["auto_disable_time"] = auto_disable_time.isoformat()
            elif not new_state:
                # Clear auto-disable when turning off
                current_settings["auto_disable_time"] = None
            
            session["ai_mode_settings"] = current_settings
            
            logger.info(f"User {user_id} toggled AI mode: {new_state}" + 
                       (f" for {duration_minutes} minutes" if duration_minutes else ""))
            
            # Emit real-time update
            socketio.emit('ai_mode_changed', {
                'active': new_state,
                'auto_disable_time': current_settings.get("auto_disable_time")
            }, room=f"user_{user_id}")
            
            return jsonify({
                "ai_mode_active": new_state,
                "auto_disable_time": current_settings.get("auto_disable_time"),
                "message": f"AI mode {'enabled' if new_state else 'disabled'}"
            })
            
        except Exception as e:
            logger.error(f"Error toggling AI mode: {e}")
            return jsonify({"error": "Failed to toggle AI mode"}), 500
    
    @app.route("/api/ai-mode/status")
    def ai_mode_status():
        """Get current AI mode status"""
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        
        settings = session.get("ai_mode_settings", {})
        return jsonify({
            "ai_mode_active": settings.get("active", False),
            "user_id": user_id,
            "auto_disable_time": settings.get("auto_disable_time"),
            "spam_sensitivity": settings.get("spam_sensitivity", "medium"),
            "recording_enabled": settings.get("recording_enabled", False)
        })
    
    # Register blueprints with API prefix
    app.register_blueprint(auth_controller.bp, url_prefix="/api/auth")
    app.register_blueprint(copilot_controller.bp, url_prefix="/api/copilot")
    app.register_blueprint(feed_controller.bp, url_prefix="/api/feed")
    app.register_blueprint(contacts_controller.bp, url_prefix="/api/contacts")
    app.register_blueprint(calls_controller.bp, url_prefix="/api/calls")
    app.register_blueprint(texts_controller.bp, url_prefix="/api/texts")
    app.register_blueprint(report_controller.bp, url_prefix="/api/reports")
    app.register_blueprint(webhooks_controller.bp, url_prefix="/api/webhooks")
    
    # Main dashboard route (web interface)
    @app.route("/")
    def dashboard():
        """Main dashboard page"""
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")
        
        try:
            # Get dashboard data
            dashboard_data = {
                "user_id": user_id,
                "ai_mode_active": session.get("ai_mode_settings", {}).get("active", False),
                "recent_calls": [],
                "recent_texts": [],
                "weekly_stats": {},
                "spam_blocked": 0
            }
            
            # Render dashboard template
            return render_template("dashboard.html", data=dashboard_data)
            
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return render_template("error.html", error="Dashboard unavailable"), 500
    
    # Authentication routes (web interface)
    @app.route("/login")
    def login_page():
        """Login page"""
        if session.get("user_id"):
            return redirect("/")
        return render_template("auth/login.html")
        
    @app.route("/register")
    def register_page():
        """Registration page"""
        if session.get("user_id"):
            return redirect("/")
        return render_template("auth/register.html")
    
    # Feature pages (web interface)
    @app.route("/contacts")
    def contacts_page():
        """Important contacts management page"""
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("contacts.html")
    
    @app.route("/feed")
    def feed_page():
        """AI instruction feed page"""
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("feed.html")
    
    @app.route("/calls")
    def calls_page():
        """Call logs and transcripts page"""
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("calls.html")
    
    @app.route("/texts")
    def texts_page():
        """Text messages page"""
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("texts.html")
    
    @app.route("/instructions")
    def instructions_page():
        """AI instructions page"""
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("instructions.html")
    
    @app.route("/analytics")
    def analytics_page():
        """Analytics and insights page"""
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("analytics.html")
    
    @app.route("/reports")
    def reports_page():
        """Weekly reports page"""
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("reports.html")
    
    @app.route("/voice-training")
    def voice_training_page():
        """Voice training page"""
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("voice_training.html")
    
    @app.route("/settings")
    def settings_page():
        """Settings and preferences page"""
        if not session.get("user_id"):
            return redirect("/login")
        return render_template("settings.html")
        
    
    @app.route("/logout")
    def logout():
        """Logout and clear session"""
        session.clear()
        return redirect("/login")
    
    # API status endpoint
    @app.route("/api/status")
    def api_status():
        """API status endpoint with more detailed information"""
        try:
            user_id = session.get("user_id")
            
            status_info = {
                "api_version": "v1",
                "service": "communicator-copilot-api",
                "authenticated": bool(user_id),
                "features": {
                    "ai_mode": True,
                    "voice_cloning": app.config.get("VOICE_CLONING_ENABLED", True),
                    "spam_detection": app.config.get("SPAM_DETECTION_ENABLED", True),
                    "call_transcription": True,
                    "text_handling": True,
                    "analytics": True,
                    "weekly_reports": True
                },
                "integrations": {
                    "database": bool(g.db_manager),
                    "speech_to_text": True,
                    "text_to_speech": True,
                    "caller_id": True
                }
            }
            
            if user_id:
                # Add user-specific status if authenticated
                settings = session.get("ai_mode_settings", {})
                status_info["user"] = {
                    "id": user_id,
                    "ai_mode_active": settings.get("active", False),
                    "voice_model_trained": settings.get("voice_model_id") is not None
                }
            
            return status_info
            
        except Exception as e:
            logger.error(f"API status check failed: {e}")
            return {"error": "Status check failed"}, 500
    
    # Import missing modules for web routes
    try:
        from flask import render_template, redirect, request
    except ImportError:
        logger.warning("Flask template rendering not available")
        
        # Fallback for API-only mode
        @app.route("/")
        def api_root():
            return {
                "service": "communicator-copilot",
                "version": "1.0.0",
                "api_base": "/api",
                "documentation": "/api/docs"
            }
    
    logger.info("Application initialization complete")
    return app

# Development server entry point
if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        debug=app.config.get("DEBUG", False)
    )

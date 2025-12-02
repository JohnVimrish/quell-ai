import os
# Ensure Transformers does not import torchvision/TensorFlow (not needed for our CPU-only text use case)
os.environ.setdefault("TRANSFORMERS_NO_TORCHVISION", "1")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
import logging
from datetime import datetime, timedelta

from flask import Flask, session, g, redirect, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, join_room

from api.utils.config import Config
from api.utils.logging import LoggerManager
from api.utils.query_manager import QueryManager
# Archived: spam detector temporarily disabled (Oct 2025)
try:
    from api.models.spam_detector import AdvancedSpamDetector as SpamDetector
except Exception:  # Module archived or unavailable
    SpamDetector = None  # type: ignore
from api.models.rag_system import RAGSystem
from api.models.voice_model import VoiceModel
from api.services.embedding_queue import EmbeddingQueue
from app.asset_loader import asset_url, asset_css, reset_manifest_cache
from .controllers import (
    feed_controller,
    documents_controller,
    auth_controller,
    labs_controller,
)
from flask import send_from_directory


def create_app(config_override=None):
    """Create and configure the Flask application."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, "templates")
    static_dir = os.path.join(project_root, "static")
    frontend_root = os.path.abspath(os.path.join(project_root, "..", "frontend"))
    legacy_dir = os.path.join(frontend_root, "legacy")
    assets_dir = os.path.join(frontend_root, "public", "assets")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path="/static",
    )

    # Make Vite asset helpers available to Jinja templates
    app.jinja_env.globals.update(asset_url=asset_url, asset_css=asset_css)

    # In development we want live reload, so do not cache the manifest
    if app.debug:
        reset_manifest_cache()

    # Base React shell routes
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def index(path):
        """Serve SPA shell; React router handles internal navigation."""
        if path.startswith("api/"):
            return jsonify({"error": "Unknown API endpoint"}), 404
        return render_template(
            "base.html",
            is_debug=app.debug,
            vite_dev_url=app.config.get("FRONTEND_DEV_URL", "http://localhost:5173"),
        )

    # Initialize SocketIO for real-time features
    message_queue_env = os.getenv("SOCKETIO_MESSAGE_QUEUE") or os.getenv("CELERY_BROKER_URL")
    message_queue = message_queue_env.strip() if message_queue_env and message_queue_env.strip() else None
    try:
        socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode="threading",
            message_queue=message_queue,
        )
    except Exception as exc:
        logging.getLogger(__name__).warning("SocketIO message queue unavailable (%s). Falling back to local mode.", exc)
        socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode="threading",
            message_queue=None,
        )

    try:
        cfg = config_override or Config.load()
        app.config["APP_CONFIG"] = cfg
        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", os.urandom(24))
        app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
        app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

        # Initialize Query Manager for centralized query management
        queries_path = os.path.join(project_root, "config", "queries.json")
        app.config["QUERY_MANAGER"] = QueryManager(queries_path)

        app.config.update(
            AI_MODEL_PATH=os.getenv("AI_MODEL_PATH", "models/"),
            VOICE_SAMPLES_PATH=os.getenv("VOICE_SAMPLES_PATH", "voice_samples/"),
            TRANSCRIPTS_PATH=os.getenv("TRANSCRIPTS_PATH", "transcripts/"),
            CONVERSATION_LAB_UPLOAD_DIR=os.getenv(
                "CONVERSATION_LAB_UPLOAD_DIR",
                os.path.join(project_root, "uploads", "conversation_lab"),
            ),
            SOCKETIO_MESSAGE_QUEUE=message_queue,
            FRONTEND_DEV_URL=os.getenv("FRONTEND_DEV_URL", "http://localhost:5173"),
            DATABASE_URL= cfg.database_url,
            DEBUG=cfg.debug,
            FEED_ACTIVE_DAYS=int(os.getenv("FEED_ACTIVE_DAYS", 7)),
            FEED_ARCHIVE_DAYS=int(os.getenv("FEED_ARCHIVE_DAYS", 7)),
            AI_MODE_MAX_DURATION=int(os.getenv("AI_MODE_MAX_DURATION", 480)),
            AI_DISCLOSURE_REQUIRED=os.getenv("AI_DISCLOSURE_REQUIRED", "true").lower() == "true",
            VOICE_CLONING_ENABLED=os.getenv("VOICE_CLONING_ENABLED", "true").lower() == "true",
            VOICE_DISCLOSURE_REQUIRED=os.getenv("VOICE_DISCLOSURE_REQUIRED", "true").lower() == "true",
            SPAM_DETECTION_ENABLED=os.getenv("SPAM_DETECTION_ENABLED", "true").lower() == "true",
            SPAM_SENSITIVITY_DEFAULT=os.getenv("SPAM_SENSITIVITY_DEFAULT", "medium"),
            CALL_RECORDING_ENABLED=os.getenv("CALL_RECORDING_ENABLED", "false").lower() == "true",
            RECORDING_CONSENT_REQUIRED=os.getenv("RECORDING_CONSENT_REQUIRED", "true").lower() == "true",
        )
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).exception("Error loading configuration")
        raise exc

    # Logging
    try:
        logger_manager = LoggerManager()
        logger_manager.configure(cfg.logging)
    except Exception as exc:  # noqa: BLE001
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).warning("Logging configuration failed: %s", exc)

    CORS(
        app,
        supports_credentials=True,
        origins=[
            app.config["FRONTEND_DEV_URL"],
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
    )

    # Database (SQLAlchemy used elsewhere; psycopg pool archived)
    app.config["DB_MANAGER"] = None

    # AI Models
    try:
        # Import here after environment flags are set
        from api.models.ollama_service import OllamaService
        # Archived feature: Spam detector (Oct 2025)
        if app.config["SPAM_DETECTION_ENABLED"] and SpamDetector is not None:
            app.config["SPAM_DETECTOR"] = SpamDetector(cfg)
        else:
            app.config["SPAM_DETECTOR"] = None

        ollama_model_path = os.getenv(
            "OLLAMA_MODEL_PATH",
            "C:/Users/033690343/OneDrive - csulb/Models-LLM/Llama-3.2-1B-Instruct"
        )
        ollama_embedding_dim = int(os.getenv("OLLAMA_EMBEDDING_DIM", "384"))
        ollama_service = OllamaService(
            model_path=ollama_model_path,
            embedding_dim=ollama_embedding_dim
        )
        embedding_queue = None
        if ollama_service and ollama_service.is_available():
            embed_workers = int(os.getenv("EMBED_QUEUE_WORKERS", "2"))
            embedding_queue = EmbeddingQueue(
                ollama_service,
                max_workers=max(1, embed_workers),
            )
        app.config["OLLAMA_SERVICE"] = ollama_service
        app.config["EMBEDDING_QUEUE"] = embedding_queue
        app.config["RAG_SYSTEM"] = RAGSystem(cfg, ollama_service, embedding_queue)

        if app.config["VOICE_CLONING_ENABLED"]:
            app.config["VOICE_MODEL"] = VoiceModel()
        else:
            app.config["VOICE_MODEL"] = None
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).exception("AI model initialization failed")
        app.config.update(
            SPAM_DETECTOR=None,
            RAG_SYSTEM=None,
            VOICE_MODEL=None,
            OLLAMA_SERVICE=None,
            EMBEDDING_QUEUE=None,
        )

    os.makedirs(app.config["AI_MODEL_PATH"], exist_ok=True)
    os.makedirs(app.config["VOICE_SAMPLES_PATH"], exist_ok=True)
    os.makedirs(app.config["TRANSCRIPTS_PATH"], exist_ok=True)
    os.makedirs(app.config["CONVERSATION_LAB_UPLOAD_DIR"], exist_ok=True)

    @socketio.on("join_ingest_room")
    def join_ingest_room(data):  # type: ignore
        session_identifier = (data or {}).get("sessionId")
        if session_identifier:
            join_room(f"ingest:{session_identifier}")

    @app.before_request
    def before_request():  # noqa: D401
        print('before request')
        g.config = app.config.get("APP_CONFIG")
        g.db_manager = app.config.get("DB_MANAGER")
        g.spam_detector = app.config.get("SPAM_DETECTOR")
        g.rag_system = app.config.get("RAG_SYSTEM")
        g.voice_model = app.config.get("VOICE_MODEL")
        g.ollama_service = app.config.get("OLLAMA_SERVICE")
        g.query_manager = app.config.get("QUERY_MANAGER")
        session.permanent = True

    @app.after_request
    def after_request(response):  # noqa: D401
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if request.path.startswith("/api/"):
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    @app.errorhandler(404)
    def not_found(error):  # noqa: D401
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found", "code": 404}), 404
        return render_template(
            "base.html",
            is_debug=app.debug,
            vite_dev_url=app.config.get("FRONTEND_DEV_URL", "http://localhost:5173"),
        ), 404

    @app.errorhandler(500)
    def internal_error(error):  # noqa: D401
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error", "code": 500}), 500
        return render_template(
            "base.html",
            is_debug=app.debug,
            vite_dev_url=app.config.get("FRONTEND_DEV_URL", "http://localhost:5173"),
        ), 500



    # Register API blueprints
    app.register_blueprint(auth_controller.bp, url_prefix="/api/auth")
    app.register_blueprint(feed_controller.bp, url_prefix="/api/feed")
    app.register_blueprint(documents_controller.bp, url_prefix="/api/documents")
    app.register_blueprint(labs_controller.bp, url_prefix="/api")

    # Simple API status endpoint
    @app.route("/api/status")
    def api_status():
        return {
            "api_version": "v1",
            "service": "communicator-copilot-api",
            "authenticated": bool(session.get("user_id")),
        }

    app.config["LEGACY_STATIC_ROOT"] = legacy_dir
    app.config["PUBLIC_ASSETS_ROOT"] = assets_dir

    @app.route('/legacy/<path:filename>')
    def serve_legacy(filename):
        """Serve legacy HTML files"""
        root = app.config.get("LEGACY_STATIC_ROOT")
        if not root:
            return jsonify({"error": "Legacy directory not configured"}), 500
        return send_from_directory(root, filename)

    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        """Serve static assets"""
        root = app.config.get("PUBLIC_ASSETS_ROOT")
        if not root:
            return jsonify({"error": "Assets directory not configured"}), 500
        return send_from_directory(root, filename)
    
    
    # Start the application
    return app


import os
from flask import Flask, g, request
from api.utils.config import Config
from api.utils.logging import configure_logging, logger
import time, uuid
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

def create_app() -> Flask:
    app = Flask(__name__, static_folder="../public", template_folder="templates")
    config = Config.load()
    app.config["APP_CONFIG"] = config
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
    configure_logging(config.logging)
    logger.info("app_initialized", extra={"event": "app_initialized"})

    # Blueprints
    app.register_blueprint(feed_controller.bp, url_prefix="/api/feed")
    app.register_blueprint(copilot_controller.bp, url_prefix="/api/mode")
    app.register_blueprint(contacts_controller.bp, url_prefix="/api/contacts")
    app.register_blueprint(calls_controller.bp, url_prefix="/api/calls")
    app.register_blueprint(texts_controller.bp, url_prefix="/api/texts")
    app.register_blueprint(report_controller.bp, url_prefix="/api/report")
    app.register_blueprint(webhooks_controller.bp, url_prefix="/webhooks")
    app.register_blueprint(auth_controller.bp, url_prefix="/api/auth")

    @app.before_request
    def _req_start():
        g.request_id = str(uuid.uuid4())
        g._start_time = time.perf_counter()
        try:
            logger.info("request_started", extra={"event": "request_started"})
        except Exception:
            pass

    @app.after_request
    def _req_end(resp):
        try:
            start = getattr(g, "_start_time", None)
            if start is not None:
                dur = int((time.perf_counter() - start) * 1000)
            else:
                dur = 0
            logger.info(
                "request_completed",
                extra={
                    "event": "request_completed",
                    "status": resp.status_code,
                    "duration_ms": dur,
                    "content_length": resp.calculate_content_length() if hasattr(resp, "calculate_content_length") else None,
                },
            )
        except Exception:
            pass
        # Propagate correlation id to client
        try:
            rid = getattr(g, "request_id", "")
            if rid:
                resp.headers["X-Request-ID"] = rid
        except Exception:
            pass
        return resp

    @app.teardown_request
    def _req_teardown(exc):
        if exc:
            try:
                logger.exception("request_failed", extra={"event": "request_failed"})
            except Exception:
                pass

    @app.errorhandler(Exception)
    def _error_handler(e):
        try:
            logger.exception("unhandled_exception", extra={"event": "unhandled_exception"})
        except Exception:
            pass
        return {"error": "internal_error"}, 500

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/")
    def home():
        return app.send_static_file("index.html") if (app.static_folder) else {"ok": True}

    return app

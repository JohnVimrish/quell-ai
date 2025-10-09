"""Status and health monitoring endpoints for the API service."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify

bp = Blueprint("status", __name__)


def build_health_payload() -> Dict[str, Any]:
    """Collect a runtime health snapshot for the service."""
    config = current_app.config
    now = datetime.utcnow()

    started_at = config.get("STARTED_AT")
    uptime_seconds = None
    if isinstance(started_at, datetime):
        uptime_seconds = int((now - started_at).total_seconds())

    overall_status = "ok"
    db_info: Dict[str, Any] = {
        "status": "unavailable",
        "message": "database manager not configured",
    }

    db_manager = config.get("DB_MANAGER")
    if db_manager is not None and getattr(db_manager, "pool", None) is None:
        db_info = {
            "status": "unavailable",
            "message": "database pool not initialised",
        }
        db_manager = None

    if db_manager is not None:
        began = time.perf_counter()
        try:
            db_ok = db_manager.test_connection()
        except Exception as exc:  # noqa: BLE001 - surface the failure message
            overall_status = "degraded"
            db_info = {
                "status": "error",
                "message": str(exc),
            }
        else:
            latency_ms = int((time.perf_counter() - began) * 1000)
            db_info = {
                "status": "ok" if db_ok else "degraded",
                "latency_ms": latency_ms,
            }
            if not db_ok:
                overall_status = "degraded"
                db_info["message"] = "connection test returned False"
    else:
        db_info = {
            "status": "unavailable",
            "message": db_info["message"],
        }

    cfg = config.get("APP_CONFIG")
    providers = []
    if cfg is not None and getattr(cfg, "providers", None):
        providers = sorted(cfg.providers.keys())

    features = {
        "spam_detection": bool(config.get("SPAM_DETECTOR")),
        "retrieval_augmented_generation": bool(config.get("RAG_SYSTEM")),
        "voice_cloning": bool(config.get("VOICE_MODEL")),
    }

    environment = {
        "debug": bool(config.get("DEBUG")),
        "environment": config.get("FLASK_ENV"),
    }

    return {
        "status": overall_status,
        "timestamp": now.isoformat() + "Z",
        "uptime_seconds": uptime_seconds,
        "components": {
            "database": db_info,
        },
        "features": features,
        "providers": providers,
        "environment": environment,
    }


@bp.get("/health")
def health() -> Any:  # type: ignore[override]
    """Detailed health report for monitoring dashboards."""
    return jsonify(build_health_payload())

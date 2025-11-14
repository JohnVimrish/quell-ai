from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, session

from api.repositories.settings_repo import SettingsRepository

bp = Blueprint("settings", __name__)


def require_auth():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id


@bp.get("")
def get_settings():
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = SettingsRepository(cfg.database_url)
    data = repo.get_settings(user_id)
    return jsonify(data)


@bp.put("")
def update_settings():
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "invalid JSON data"}), 400

    cfg = current_app.config["APP_CONFIG"]
    repo = SettingsRepository(cfg.database_url)
    data = repo.update_settings(user_id, payload)
    return jsonify(data)


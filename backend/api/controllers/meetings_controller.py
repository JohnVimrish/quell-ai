from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, session

from api.repositories.meetings_repo import MeetingsRepository

bp = Blueprint("meetings", __name__)


def require_auth():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id


@bp.get("")
def list_meetings():
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = MeetingsRepository(cfg.database_url, cfg.queries)

    page = int(request.args.get("page", 1))
    limit = min(int(request.args.get("limit", 25)), 100)
    status = request.args.get("status")
    date_from = request.args.get("from")
    date_to = request.args.get("to")

    filters = {"user_id": user_id}
    if status:
        filters["status"] = status
    if date_from:
        filters["date_from"] = datetime.fromisoformat(date_from)
    if date_to:
        filters["date_to"] = datetime.fromisoformat(date_to)

    meetings = repo.list_meetings(filters, page, limit)
    total = repo.count_meetings(filters)
    return jsonify(
        {
            "meetings": meetings,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            },
        }
    )


@bp.post("")
def schedule_meeting():
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "invalid JSON data"}), 400

    cfg = current_app.config["APP_CONFIG"]
    repo = MeetingsRepository(cfg.database_url, cfg.queries)

    meeting_payload = {
        "user_id": user_id,
        "platform": payload.get("platform", "zoom"),
        "subject": payload.get("title"),
        "counterpart_name": payload.get("organizer"),
        "counterpart_identifier": payload.get("meeting_id"),
        "external_session_id": payload.get("external_session_id"),
        "status": payload.get("status", "scheduled"),
        "scheduled_start": payload.get("scheduled_start"),
        "scheduled_end": payload.get("scheduled_end"),
        "session_metadata": {
            "agenda": payload.get("agenda"),
            "auto_join": payload.get("auto_join", False),
            "requires_voice_clone": payload.get("requires_voice_clone", False),
        },
    }

    meeting_id = repo.create_meeting(meeting_payload)
    if not meeting_id:
        return jsonify({"error": "failed to schedule meeting"}), 500

    return jsonify({"meeting_id": meeting_id}), 201


@bp.get("/<int:meeting_id>")
def get_meeting(meeting_id: int):
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = MeetingsRepository(cfg.database_url, cfg.queries)
    meeting = repo.get_meeting(meeting_id, user_id)
    if not meeting:
        return jsonify({"error": "meeting not found"}), 404
    return jsonify(meeting)


@bp.put("/<int:meeting_id>")
def update_meeting(meeting_id: int):
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "invalid JSON data"}), 400

    cfg = current_app.config["APP_CONFIG"]
    repo = MeetingsRepository(cfg.database_url, cfg.queries)

    success = repo.update_meeting(meeting_id, payload)
    if not success:
        return jsonify({"error": "update failed"}), 404

    meeting = repo.get_meeting(meeting_id, user_id)
    return jsonify(meeting)


@bp.delete("/<int:meeting_id>")
def delete_meeting(meeting_id: int):
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = MeetingsRepository(cfg.database_url, cfg.queries)

    success = repo.delete_meeting(meeting_id, user_id)
    if not success:
        return jsonify({"error": "meeting not found"}), 404

    return jsonify({"message": "meeting deleted"})


@bp.get("/summary/weekly")
def weekly_summary():
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = MeetingsRepository(cfg.database_url, cfg.queries)
    summary = repo.get_weekly_summary(user_id)
    return jsonify(summary)


@bp.get("/<int:meeting_id>/transcript")
def meeting_transcript(meeting_id: int):
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = MeetingsRepository(cfg.database_url, cfg.queries)
    meeting = repo.get_meeting(meeting_id, user_id)
    if not meeting:
        return jsonify({"error": "meeting not found"}), 404

    transcript = repo.get_transcript(meeting_id)
    return jsonify({"transcript": transcript})


@bp.get("/<int:meeting_id>/participants")
def meeting_participants(meeting_id: int):
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = MeetingsRepository(cfg.database_url, cfg.queries)
    meeting = repo.get_meeting(meeting_id, user_id)
    if not meeting:
        return jsonify({"error": "meeting not found"}), 404

    participants = repo.get_participants(meeting_id)
    return jsonify({"participants": participants})


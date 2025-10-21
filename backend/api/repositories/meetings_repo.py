from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from api.repositories.communication_repo import CommunicationRepository

logger = logging.getLogger(__name__)


class MeetingsRepository:
    """Meeting-specific helpers over the shared communication repository."""

    def __init__(self, database_url: str, _queries_config: Optional[Dict] = None):
        self.repo = CommunicationRepository(database_url)

    def list_meetings(self, filters: Dict, page: int, limit: int) -> List[Dict]:
        scoped = dict(filters)
        scoped["session_type"] = "meeting"
        return self.repo.list_sessions(scoped, page, limit)

    def count_meetings(self, filters: Dict) -> int:
        scoped = dict(filters)
        scoped["session_type"] = "meeting"
        return self.repo.count_sessions(scoped)

    def get_meeting(self, meeting_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
        return self.repo.get_session(meeting_id, user_id)

    def create_meeting(self, payload: Dict) -> Optional[int]:
        payload = dict(payload)
        payload["session_type"] = "meeting"
        payload.setdefault("channel", payload.get("platform", "zoom"))
        payload.setdefault("started_at", payload.get("scheduled_start") or datetime.utcnow())
        payload.setdefault("status", payload.get("status", "scheduled"))
        payload.setdefault("session_metadata", {})
        payload["session_metadata"]["scheduled_start"] = payload.get("scheduled_start")
        payload["session_metadata"]["scheduled_end"] = payload.get("scheduled_end")
        return self.repo.create_session(payload)

    def update_meeting(self, meeting_id: int, payload: Dict) -> bool:
        return self.repo.update_session(meeting_id, payload)

    def delete_meeting(self, meeting_id: int, user_id: int) -> bool:
        return self.repo.delete_session(meeting_id, user_id)

    def add_transcript(self, meeting_id: int, payload: Dict) -> Optional[int]:
        return self.repo.add_transcript(meeting_id, payload)

    def get_transcript(self, meeting_id: int) -> Optional[Dict]:
        return self.repo.get_transcript(meeting_id)

    def add_participant(self, meeting_id: int, payload: Dict) -> Optional[int]:
        return self.repo.add_participant(meeting_id, payload)

    def get_participants(self, meeting_id: int) -> List[Dict]:
        return self.repo.get_participants(meeting_id)

    def add_message(self, meeting_id: int, payload: Dict) -> Optional[int]:
        return self.repo.add_message(meeting_id, payload)

    def get_recent_meetings(self, user_id: int, limit: int = 10) -> List[Dict]:
        return self.repo.get_recent_sessions(user_id, "meeting", limit)

    def get_weekly_summary(self, user_id: int) -> Dict:
        end = datetime.utcnow()
        start = end - timedelta(days=7)
        filters = {
            "user_id": user_id,
            "session_type": "meeting",
            "date_from": start,
            "date_to": end,
        }
        meetings = self.repo.list_sessions(filters, page=1, limit=200)
        total_duration = sum(m.get("duration_seconds") or 0 for m in meetings)
        ai_attended = [m for m in meetings if m.get("ai_participated")]
        return {
            "total_meetings": len(meetings),
            "ai_attended": len(ai_attended),
            "total_duration_seconds": total_duration,
            "meetings": meetings,
        }


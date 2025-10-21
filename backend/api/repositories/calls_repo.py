from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.repositories.communication_repo import CommunicationRepository
from functionalities.communication_session import CommunicationSession

logger = logging.getLogger(__name__)


class CallsRepository:
    """High-level helper over CommunicationRepository for phone calls."""

    def __init__(self, database_url: str, _queries_config: Optional[Dict] = None):
        self.database_url = database_url
        self.repo = CommunicationRepository(database_url)
        self._engine = create_engine(database_url, future=True)
        self._session_factory = sessionmaker(
            bind=self._engine, autoflush=False, expire_on_commit=False
        )

    # ------------------------------------------------------------------
    # Query primitives
    # ------------------------------------------------------------------
    def list_calls(self, filters: Dict, page: int, limit: int) -> List[Dict]:
        scoped_filters = dict(filters)
        scoped_filters["session_type"] = "call"
        if call_type := scoped_filters.pop("call_type", None):
            scoped_filters["direction"] = call_type
        return self.repo.list_sessions(scoped_filters, page, limit)

    def count_calls(self, filters: Dict) -> int:
        scoped_filters = dict(filters)
        scoped_filters["session_type"] = "call"
        if call_type := scoped_filters.pop("call_type", None):
            scoped_filters["direction"] = call_type
        return self.repo.count_sessions(scoped_filters)

    def get_call(self, call_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
        return self.repo.get_session(call_id, user_id)

    def get_recent_calls(
        self, user_id: int, limit: int = 20, include_spam: bool = False
    ) -> List[Dict]:
        calls = self.repo.get_recent_sessions(user_id, "call", limit)
        if include_spam:
            return calls
        return [
            call
            for call in calls
            if not (call.get("session_metadata", {}).get("is_spam") is True)
        ]

    def get_calls_by_date_range(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        filters = {
            "user_id": user_id,
            "session_type": "call",
            "date_from": start_date,
            "date_to": end_date,
        }
        return self.repo.list_sessions(filters, page=1, limit=1000)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    def create_call(self, call_data: Dict) -> Optional[int]:
        try:
            metadata = {
                "from_number": call_data.get("from_number") or call_data.get("caller_number"),
                "to_number": call_data.get("to_number") or call_data.get("callee_number"),
                "is_spam": call_data.get("is_spam"),
                "spam_score": call_data.get("spam_score"),
                "notes": call_data.get("notes"),
                "tags": call_data.get("tags"),
            }
            payload = {
                "user_id": call_data["user_id"],
                "session_type": "call",
                "channel": call_data.get("channel", "phone"),
                "external_session_id": call_data.get("external_call_id"),
                "subject": call_data.get("subject"),
                "counterpart_name": call_data.get("caller_name"),
                "counterpart_identifier": _resolve_counterpart_identifier(call_data),
                "counterpart_type": "phone",
                "direction": call_data.get("direction") or call_data.get("call_type"),
                "status": call_data.get("status", "completed"),
                "ai_participated": call_data.get("ai_participated", False),
                "ai_role": call_data.get("ai_role", "delegate"),
                "disclosure_sent": call_data.get("disclosure_sent", True),
                "started_at": call_data.get("started_at") or datetime.utcnow(),
                "ended_at": call_data.get("ended_at"),
                "duration_seconds": call_data.get("duration_seconds"),
                "summary_text": call_data.get("summary_text"),
                "summary_bullets": call_data.get("summary_bullets"),
                "sentiment_score": call_data.get("sentiment_score"),
                "topics": call_data.get("topics"),
                "action_items": call_data.get("action_items"),
                "recording_url": call_data.get("recording_url"),
                "session_metadata": metadata,
                "ai_decisions": call_data.get("ai_decisions"),
                "retention_expires_at": call_data.get("retention_expires_at"),
            }

            call_id = self.repo.create_session(payload)
            if not call_id:
                return None

            for participant in call_data.get("participants", []) or []:
                self.add_call_participant(call_id, participant)

            transcript = call_data.get("transcript")
            if transcript:
                transcript_payload = {"transcript_text": transcript}
                transcript_payload.update(call_data.get("transcript_metadata", {}))
                self.add_call_transcript(call_id, transcript_payload)

            return call_id
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to create call: %s", exc)
            return None

    def update_call(self, call_id: int, update_data: Dict) -> bool:
        try:
            safe_update = dict(update_data)
            metadata_updates = safe_update.pop("session_metadata", {})

            # Map legacy fields into session metadata
            legacy_metadata_fields = ("is_spam", "spam_score", "notes", "tags")
            for field in legacy_metadata_fields:
                if field in safe_update:
                    metadata_updates[field] = safe_update.pop(field)

            for number_field in ("from_number", "to_number"):
                if number_field in safe_update:
                    metadata_updates[number_field] = safe_update.pop(number_field)

            transcript_text = safe_update.pop("transcript", None)
            if transcript_text is not None:
                self.repo.upsert_transcript(
                    call_id, {"transcript_text": transcript_text}
                )

            if metadata_updates:
                with self._session_factory() as sess:
                    record = sess.get(CommunicationSession, call_id)
                    if not record:
                        return False
                    current = record.session_metadata or {}
                    current.update(metadata_updates)
                    safe_update["session_metadata"] = current

            return self.repo.update_session(call_id, safe_update)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to update call %s: %s", call_id, exc)
            return False

    def delete_call(self, call_id: int, user_id: int) -> bool:
        return self.repo.delete_session(call_id, user_id)

    def bulk_delete_calls(self, user_id: int, call_ids: List[int]) -> int:
        return self.repo.bulk_delete_sessions(user_id, call_ids)

    # ------------------------------------------------------------------
    # Analytics & insights
    # ------------------------------------------------------------------
    def get_call_statistics(self, user_id: int, days: int = 30) -> Dict:
        date_from = datetime.utcnow() - timedelta(days=days)
        calls = self.get_calls_by_date_range(user_id, date_from, datetime.utcnow())

        total_duration = sum(call.get("duration_seconds") or 0 for call in calls)
        incoming = [c for c in calls if c.get("direction") == "incoming"]
        outgoing = [c for c in calls if c.get("direction") == "outgoing"]

        spam_calls = [
            c for c in calls if c.get("session_metadata", {}).get("is_spam") is True
        ]

        return {
            "total_calls": len(calls),
            "incoming_calls": len(incoming),
            "outgoing_calls": len(outgoing),
            "spam_calls": len(spam_calls),
            "ai_handled": len([c for c in calls if c.get("ai_participated")]),
            "total_duration_seconds": total_duration,
        }

    def get_call_stats(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> Dict:
        calls = self.get_calls_by_date_range(user_id, start_date, end_date)
        return {
            "total_calls": len(calls),
            "ai_handled": len([c for c in calls if c.get("ai_participated")]),
            "spam_calls": len(
                [c for c in calls if c.get("session_metadata", {}).get("is_spam")]
            ),
            "average_duration": (
                sum(c.get("duration_seconds") or 0 for c in calls) / len(calls)
                if calls
                else 0
            ),
            "calls": calls,
        }

    def search_calls(
        self,
        user_id: int,
        query: str,
        page: int,
        limit: int,
    ) -> List[Dict]:
        return self.repo.search_sessions(user_id, query, "call", page, limit)

    def count_search_results(self, user_id: int, query: str) -> int:
        return self.repo.count_search_results(user_id, query, "call")

    def mark_as_spam(self, call_id: int, user_id: int) -> bool:
        call = self.get_call(call_id, user_id)
        if not call:
            return False
        metadata = call.get("session_metadata") or {}
        metadata.update({"is_spam": True})
        return self.update_call(call_id, {"status": "flagged", "session_metadata": metadata})

    def unmark_spam(self, call_id: int, user_id: int) -> bool:
        call = self.get_call(call_id, user_id)
        if not call:
            return False
        metadata = call.get("session_metadata") or {}
        metadata.pop("is_spam", None)
        return self.update_call(call_id, {"status": "completed", "session_metadata": metadata})

    def mark_call_as_important(self, call_id: int, user_id: int) -> bool:
        call = self.get_call(call_id, user_id)
        if not call:
            return False
        metadata = call.get("session_metadata") or {}
        metadata["priority"] = "important"
        return self.update_call(call_id, {"session_metadata": metadata})

    def add_call_transcript(self, call_id: int, transcript_data: Dict) -> Optional[int]:
        return self.repo.add_transcript(call_id, transcript_data)

    def get_call_transcript(self, call_id: int) -> Optional[Dict]:
        return self.repo.get_transcript(call_id)

    def add_call_participant(self, call_id: int, participant_data: Dict) -> Optional[int]:
        return self.repo.add_participant(call_id, participant_data)

    def get_call_participants(self, call_id: int) -> List[Dict]:
        return self.repo.get_participants(call_id)

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------
    def get_call_by_external_id(self, external_id: str) -> Optional[Dict]:
        with self._session_factory() as sess:
            record = (
                sess.query(CommunicationSession)
                .filter(
                    CommunicationSession.session_type == "call",
                    CommunicationSession.external_session_id == external_id,
                )
                .first()
            )
            return record.to_dict() if record else None

    def get_daily_call_summary(self, user_id: int, date: datetime) -> Dict:
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        calls = self.get_calls_by_date_range(user_id, start, end)
        return {
            "date": start.date().isoformat(),
            "total_calls": len(calls),
            "incoming_calls": len([c for c in calls if c.get("direction") == "incoming"]),
            "outgoing_calls": len([c for c in calls if c.get("direction") == "outgoing"]),
            "ai_handled": len([c for c in calls if c.get("ai_participated")]),
            "total_duration_seconds": sum(c.get("duration_seconds") or 0 for c in calls),
            "calls": calls,
        }


def _resolve_counterpart_identifier(call_data: Dict) -> Optional[str]:
    direction = call_data.get("direction") or call_data.get("call_type", "incoming")
    if direction == "outgoing":
        return call_data.get("to_number") or call_data.get("callee_number")
    return call_data.get("from_number") or call_data.get("caller_number")

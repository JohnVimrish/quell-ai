from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from sqlalchemy import and_, create_engine, func, or_
from sqlalchemy.orm import Session, sessionmaker

from functionalities.communication_session import (
    CommunicationSession,
    SessionMessage,
    SessionParticipant,
    SessionTranscript,
)


class CommunicationRepository:
    """Unified repository for call, meeting, and chat session data."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True)
        self._session_factory = sessionmaker(
            bind=self.engine, autoflush=False, expire_on_commit=False
        )

    @contextmanager
    def session_scope(self) -> Iterable[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Session CRUD
    # ------------------------------------------------------------------
    def create_session(self, payload: Dict) -> Optional[int]:
        session_type = payload.get("session_type")
        if not session_type:
            raise ValueError("session_type is required")

        data = CommunicationSession(
            user_id=payload["user_id"],
            session_type=session_type,
            channel=payload.get("channel"),
            external_session_id=payload.get("external_session_id"),
            subject=payload.get("subject"),
            counterpart_name=payload.get("counterpart_name"),
            counterpart_identifier=payload.get("counterpart_identifier"),
            counterpart_type=payload.get("counterpart_type"),
            direction=payload.get("direction"),
            status=payload.get("status", "completed"),
            ai_participated=payload.get("ai_participated", False),
            ai_role=payload.get("ai_role", "delegate"),
            disclosure_sent=payload.get("disclosure_sent", False),
            started_at=_coerce_datetime(payload.get("started_at")),
            ended_at=_coerce_datetime(payload.get("ended_at")),
            duration_seconds=payload.get("duration_seconds"),
            summary_text=payload.get("summary_text"),
            summary_bullets=payload.get("summary_bullets"),
            sentiment_score=payload.get("sentiment_score"),
            topics=payload.get("topics"),
            action_items=payload.get("action_items"),
            recording_url=payload.get("recording_url"),
            session_metadata=payload.get("session_metadata"),
            ai_decisions=payload.get("ai_decisions"),
            retention_expires_at=_coerce_datetime(payload.get("retention_expires_at")),
        )

        with self.session_scope() as sess:
            sess.add(data)
            sess.flush()
            return data.id

    def update_session(self, session_id: int, payload: Dict) -> bool:
        with self.session_scope() as sess:
            record = sess.get(CommunicationSession, session_id)
            if not record:
                return False

            for key, value in payload.items():
                if key in {"started_at", "ended_at", "retention_expires_at"}:
                    value = _coerce_datetime(value)
                if hasattr(record, key):
                    setattr(record, key, value)
            return True

    def get_session(
        self, session_id: int, user_id: Optional[int] = None
    ) -> Optional[Dict]:
        with self.session_scope() as sess:
            query = sess.query(CommunicationSession).filter(
                CommunicationSession.id == session_id
            )
            if user_id:
                query = query.filter(CommunicationSession.user_id == user_id)
            record = query.first()
            return record.to_dict() if record else None

    def delete_session(self, session_id: int, user_id: int) -> bool:
        with self.session_scope() as sess:
            query = sess.query(CommunicationSession).filter(
                CommunicationSession.id == session_id,
                CommunicationSession.user_id == user_id,
            )
            record = query.first()
            if not record:
                return False
            sess.delete(record)
            return True

    def bulk_delete_sessions(self, user_id: int, session_ids: List[int]) -> int:
        if not session_ids:
            return 0

        with self.session_scope() as sess:
            deleted = (
                sess.query(CommunicationSession)
                .filter(
                    CommunicationSession.user_id == user_id,
                    CommunicationSession.id.in_(session_ids),
                )
                .delete(synchronize_session=False)
            )
            return deleted or 0

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def list_sessions(
        self, filters: Dict, page: int, limit: int
    ) -> List[Dict[str, object]]:
        with self.session_scope() as sess:
            query = self._apply_filters(sess, filters)
            rows = (
                query.order_by(CommunicationSession.started_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )
            return [row.to_dict() for row in rows]

    def count_sessions(self, filters: Dict) -> int:
        with self.session_scope() as sess:
            query = self._apply_filters(sess, filters)
            return query.count()

    def get_recent_sessions(
        self, user_id: int, session_type: str, limit: int = 20
    ) -> List[Dict[str, object]]:
        with self.session_scope() as sess:
            rows = (
                sess.query(CommunicationSession)
                .filter(
                    CommunicationSession.user_id == user_id,
                    CommunicationSession.session_type == session_type,
                )
                .order_by(CommunicationSession.started_at.desc())
                .limit(limit)
                .all()
            )
            return [row.to_dict() for row in rows]

    def search_sessions(
        self,
        user_id: int,
        query: str,
        session_type: str,
        page: int,
        limit: int,
    ) -> List[Dict[str, object]]:
        with self.session_scope() as sess:
            filters = [
                CommunicationSession.user_id == user_id,
                CommunicationSession.session_type == session_type,
                or_(
                    CommunicationSession.subject.ilike(f"%{query}%"),
                    CommunicationSession.summary_text.ilike(f"%{query}%"),
                    CommunicationSession.counterpart_name.ilike(f"%{query}%"),
                ),
            ]
            rows = (
                sess.query(CommunicationSession)
                .filter(and_(*filters))
                .order_by(CommunicationSession.started_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )
            return [row.to_dict() for row in rows]

    def count_search_results(
        self, user_id: int, query: str, session_type: str
    ) -> int:
        with self.session_scope() as sess:
            filters = [
                CommunicationSession.user_id == user_id,
                CommunicationSession.session_type == session_type,
                or_(
                    CommunicationSession.subject.ilike(f"%{query}%"),
                    CommunicationSession.summary_text.ilike(f"%{query}%"),
                    CommunicationSession.counterpart_name.ilike(f"%{query}%"),
                ),
            ]
            return (
                sess.query(func.count(CommunicationSession.id))
                .filter(and_(*filters))
                .scalar()
                or 0
            )

    # ------------------------------------------------------------------
    # Transcript / participants / messages
    # ------------------------------------------------------------------
    def add_transcript(self, session_id: int, payload: Dict) -> Optional[int]:
        with self.session_scope() as sess:
            transcript = SessionTranscript(
                session_id=session_id,
                transcript_text=payload["transcript_text"],
                provider=payload.get("provider"),
                language=payload.get("language", "en"),
                confidence=payload.get("confidence"),
                segments=payload.get("segments"),
                summary_text=payload.get("summary_text"),
                summary_bullets=payload.get("summary_bullets"),
                sentiment_score=payload.get("sentiment_score"),
                topics=payload.get("topics"),
                action_items=payload.get("action_items"),
                mindmap=payload.get("mindmap"),
                analytics=payload.get("analytics"),
            )
            sess.add(transcript)
            sess.flush()
            return transcript.id

    def upsert_transcript(self, session_id: int, payload: Dict) -> Optional[int]:
        with self.session_scope() as sess:
            record = (
                sess.query(SessionTranscript)
                .filter(SessionTranscript.session_id == session_id)
                .first()
            )
            if record:
                for key, value in payload.items():
                    setattr(record, key, value)
                sess.flush()
                return record.id
            transcript = SessionTranscript(session_id=session_id, **payload)
            sess.add(transcript)
            sess.flush()
            return transcript.id

    def get_transcript(self, session_id: int) -> Optional[Dict]:
        with self.session_scope() as sess:
            record = (
                sess.query(SessionTranscript)
                .filter(SessionTranscript.session_id == session_id)
                .first()
            )
            return record.to_dict() if record else None

    def add_participant(self, session_id: int, payload: Dict) -> Optional[int]:
        with self.session_scope() as sess:
            participant = SessionParticipant(
                session_id=session_id,
                participant_type=payload.get("participant_type", "external"),
                identifier=payload.get("identifier"),
                display_name=payload.get("display_name"),
                role=payload.get("role"),
                is_host=payload.get("is_host", False),
                joined_at=_coerce_datetime(payload.get("joined_at")),
                left_at=_coerce_datetime(payload.get("left_at")),
                participant_metadata=payload.get("metadata"),
            )
            sess.add(participant)
            sess.flush()
            return participant.id

    def get_participants(self, session_id: int) -> List[Dict[str, object]]:
        with self.session_scope() as sess:
            rows = (
                sess.query(SessionParticipant)
                .filter(SessionParticipant.session_id == session_id)
                .order_by(SessionParticipant.joined_at.asc())
                .all()
            )
            return [row.to_dict() for row in rows]

    def add_message(self, session_id: int, payload: Dict) -> Optional[int]:
        with self.session_scope() as sess:
            message = SessionMessage(
                session_id=session_id,
                participant_id=payload.get("participant_id"),
                direction=payload.get("direction", "incoming"),
                content=payload["content"],
                content_type=payload.get("content_type", "text"),
                message_metadata=payload.get("message_metadata"),
                sentiment_score=payload.get("sentiment_score"),
                is_ai_generated=payload.get("is_ai_generated", False),
                sent_at=_coerce_datetime(payload.get("sent_at")) or datetime.utcnow(),
            )
            sess.add(message)
            sess.flush()
            return message.id

    def get_messages(
        self, session_id: int, page: int, limit: int
    ) -> List[Dict[str, object]]:
        with self.session_scope() as sess:
            rows = (
                sess.query(SessionMessage)
                .filter(SessionMessage.session_id == session_id)
                .order_by(SessionMessage.sent_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )
            return [row.to_dict() for row in rows]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _apply_filters(self, sess: Session, filters: Dict):
        query = sess.query(CommunicationSession)

        if user_id := filters.get("user_id"):
            query = query.filter(CommunicationSession.user_id == user_id)

        if session_type := filters.get("session_type"):
            query = query.filter(CommunicationSession.session_type == session_type)

        if direction := filters.get("direction"):
            query = query.filter(CommunicationSession.direction == direction)

        if status := filters.get("status"):
            query = query.filter(CommunicationSession.status == status)

        if exclude_status := filters.get("exclude_status"):
            query = query.filter(CommunicationSession.status != exclude_status)

        if channel := filters.get("channel"):
            query = query.filter(CommunicationSession.channel == channel)

        if date_from := filters.get("date_from"):
            query = query.filter(
                CommunicationSession.started_at >= _coerce_datetime(date_from)
            )

        if date_to := filters.get("date_to"):
            query = query.filter(
                CommunicationSession.started_at <= _coerce_datetime(date_to)
            )

        if counterpart := filters.get("counterpart"):
            query = query.filter(
                or_(
                    CommunicationSession.counterpart_name.ilike(f"%{counterpart}%"),
                    CommunicationSession.counterpart_identifier.ilike(
                        f"%{counterpart}%"
                    ),
                )
            )

        return query


def _coerce_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None

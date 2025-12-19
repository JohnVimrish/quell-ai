from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

from api.repositories.communication_repo import CommunicationRepository
from functionalities.communication_session import (
    CommunicationSession,
    SessionMessage,
)
from functionalities.user import User

logger = logging.getLogger(__name__)


class TextsRepository:
    """Repository for SMS/chat conversations leveraging the unified session model."""

    def __init__(self, database_url: str, _queries_config: Optional[Dict] = None):
        self.database_url = database_url
        self.repo = CommunicationRepository(database_url)
        self._engine = create_engine(database_url, future=True)
        self._session_factory = sessionmaker(
            bind=self._engine, autoflush=False, expire_on_commit=False
        )

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------
    def get_conversations(
        self, user_id: int, page: int, limit: int, include_archived: bool
    ) -> List[Dict]:
        filters = {
            "user_id": user_id,
            "session_type": "chat",
        }
        if not include_archived:
            filters["exclude_status"] = "archived"
        conversations = self.repo.list_sessions(filters, page, limit)
        return [
            {
                **conv,
                "contact_id": _contact_id_from_identifier(conv.get("counterpart_identifier")),
            }
            for conv in conversations
        ]

    def count_conversations(self, user_id: int, include_archived: bool) -> int:
        filters = {
            "user_id": user_id,
            "session_type": "chat",
        }
        if not include_archived:
            filters["exclude_status"] = "archived"
        return self.repo.count_sessions(filters)

    def get_conversation_messages(
        self, user_id: int, contact_id: int, page: int, limit: int
    ) -> List[Dict]:
        with self._session_scope() as sess:
            chat_session = self._get_session_for_contact(sess, user_id, contact_id)
            if not chat_session:
                return []
            messages = (
                sess.query(SessionMessage)
                .filter(SessionMessage.session_id == chat_session.id)
                .order_by(SessionMessage.sent_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )
            return [message.to_dict() for message in messages]

    def count_conversation_messages(self, user_id: int, contact_id: int) -> int:
        with self._session_scope() as sess:
            chat_session = self._get_session_for_contact(sess, user_id, contact_id)
            if not chat_session:
                return 0
            return (
                sess.query(func.count(SessionMessage.id))
                .filter(SessionMessage.session_id == chat_session.id)
                .scalar()
                or 0
            )

    def mark_messages_as_read(self, user_id: int, contact_id: int) -> None:
        with self._session_scope() as sess:
            chat_session = self._get_session_for_contact(sess, user_id, contact_id)
            if not chat_session:
                return
            for message in (
                sess.query(SessionMessage)
                .filter(SessionMessage.session_id == chat_session.id)
                .all()
            ):
                metadata = message.message_metadata or {}
                metadata["read"] = True
                message.message_metadata = metadata

    # ------------------------------------------------------------------
    # Message CRUD
    # ------------------------------------------------------------------
    def create_message(self, message_data: Dict) -> Optional[int]:
        contact_id = message_data.get("contact_id")
        user_id = message_data["user_id"]

        with self._session_scope() as sess:
            chat_session = self._get_session_for_contact(sess, user_id, contact_id)
            if not chat_session:
                payload = {
                    "user_id": user_id,
                    "session_type": "chat",
                    "channel": message_data.get("channel", "sms"),
                    "external_session_id": message_data.get("conversation_external_id"),
                    "subject": message_data.get("subject"),
                    "counterpart_name": message_data.get("contact_name")
                    or message_data.get("phone_number"),
                    "counterpart_identifier": _identifier_for_contact(contact_id),
                    "counterpart_type": "contact",
                    "direction": "asynchronous",
                    "status": "active",
                    "started_at": message_data.get("sent_at") or datetime.utcnow(),
                    "session_metadata": {
                        "contact_id": contact_id,
                        "phone_number": message_data.get("phone_number"),
                    },
                }
                session_id = self.repo.create_session(payload)
                if not session_id:
                    return None
                chat_session = sess.get(CommunicationSession, session_id)

            participant_id = None
            if message_data.get("direction") == "incoming":
                participant_id = self._ensure_participant(
                    sess,
                    chat_session.id,
                    participant_type="external",
                    display_name=chat_session.counterpart_name,
                    identifier=message_data.get("phone_number"),
                )
            else:
                participant_id = self._ensure_participant(
                    sess,
                    chat_session.id,
                    participant_type="user",
                    display_name="User",
                    identifier=str(user_id),
                )

            metadata = {
                "status": message_data.get("status"),
                "read": message_data.get("direction") == "outgoing",
                "is_spam": message_data.get("is_spam"),
            }

            message_id = self.repo.add_message(
                chat_session.id,
                {
                    "participant_id": participant_id,
                    "direction": message_data.get("direction", "incoming"),
                    "content": message_data.get("message_body"),
                    "content_type": message_data.get("message_type", "text"),
                    "message_metadata": metadata,
                    "sent_at": message_data.get("sent_at"),
                    "is_ai_generated": message_data.get("ai_generated", False),
                },
            )

            last_sent_at = message_data.get("sent_at")
            dt_sent_at = _coerce_datetime(last_sent_at) or datetime.utcnow()
            metadata = chat_session.session_metadata or {}
            metadata["last_message_at"] = last_sent_at or dt_sent_at.isoformat()
            metadata["contact_id"] = contact_id
            chat_session.session_metadata = metadata
            chat_session.ended_at = dt_sent_at

            return message_id

    def update_message_status(
        self, message_id: int, status: str, timestamp: Optional[str]
    ) -> None:
        with self._session_scope() as sess:
            message = sess.get(SessionMessage, message_id)
            if not message:
                return
            metadata = message.message_metadata or {}
            metadata["status"] = status
            if timestamp:
                metadata["status_updated_at"] = timestamp
            message.message_metadata = metadata

    def update_message_spam_status(self, message_id: int, is_spam: bool) -> None:
        with self._session_scope() as sess:
            message = sess.get(SessionMessage, message_id)
            if not message:
                return
            metadata = message.message_metadata or {}
            metadata["is_spam"] = is_spam
            message.message_metadata = metadata

    def get_message(self, message_id: int) -> Optional[Dict]:
        with self._session_scope() as sess:
            message = sess.get(SessionMessage, message_id)
            return message.to_dict() if message else None

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search_messages(
        self,
        user_id: int,
        query: str,
        page: int,
        limit: int,
        contact_id: Optional[int] = None,
    ) -> List[Dict]:
        with self._session_scope() as sess:
            q = (
                sess.query(SessionMessage)
                .join(CommunicationSession, SessionMessage.session_id == CommunicationSession.id)
                .filter(
                    CommunicationSession.user_id == user_id,
                    CommunicationSession.session_type == "chat",
                    SessionMessage.content.ilike(f"%{query}%"),
                )
            )
            if contact_id is not None:
                identifier = _identifier_for_contact(contact_id)
                q = q.filter(CommunicationSession.counterpart_identifier == identifier)

            messages = (
                q.order_by(SessionMessage.sent_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )
            return [message.to_dict() for message in messages]

    def count_search_results(
        self, user_id: int, query: str, contact_id: Optional[int] = None
    ) -> int:
        with self._session_scope() as sess:
            q = (
                sess.query(func.count(SessionMessage.id))
                .join(CommunicationSession, SessionMessage.session_id == CommunicationSession.id)
                .filter(
                    CommunicationSession.user_id == user_id,
                    CommunicationSession.session_type == "chat",
                    SessionMessage.content.ilike(f"%{query}%"),
                )
            )
            if contact_id is not None:
                identifier = _identifier_for_contact(contact_id)
                q = q.filter(CommunicationSession.counterpart_identifier == identifier)

            return q.scalar() or 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def get_user_by_phone(self, phone_number: str) -> Optional[Dict]:
        with self._session_scope() as sess:
            user = (
                sess.query(User)
                .filter(User.phone_number == phone_number)
                .first()
            )
            return user.to_dict() if user else None

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _get_session_for_contact(
        self, sess: Session, user_id: int, contact_id: Optional[int]
    ) -> Optional[CommunicationSession]:
        identifier = _identifier_for_contact(contact_id)
        return (
            sess.query(CommunicationSession)
            .filter(
                CommunicationSession.user_id == user_id,
                CommunicationSession.session_type == "chat",
                CommunicationSession.counterpart_identifier == identifier,
            )
            .first()
        )

    def _ensure_participant(
        self,
        sess: Session,
        session_id: int,
        participant_type: str,
        display_name: Optional[str],
        identifier: Optional[str],
    ) -> Optional[int]:
        from functionalities.communication_session import SessionParticipant

        participant = (
            sess.query(SessionParticipant)
            .filter(
                SessionParticipant.session_id == session_id,
                SessionParticipant.participant_type == participant_type,
                SessionParticipant.identifier == identifier,
            )
            .first()
        )
        if participant:
            return participant.id

        participant = SessionParticipant(
            session_id=session_id,
            participant_type=participant_type,
            display_name=display_name,
            identifier=identifier,
            joined_at=datetime.utcnow(),
        )
        sess.add(participant)
        sess.flush()
        return participant.id

    @contextmanager
    def _session_scope(self):
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def _identifier_for_contact(contact_id: Optional[int]) -> str:
    return f"contact:{contact_id}" if contact_id is not None else "contact:unknown"


def _contact_id_from_identifier(identifier: Optional[str]) -> Optional[int]:
    if not identifier or not identifier.startswith("contact:"):
        return None
    _, value = identifier.split(":", 1)
    try:
        return int(value) if value != "unknown" else None
    except ValueError:
        return None


def _coerce_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None

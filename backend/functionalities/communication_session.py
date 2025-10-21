from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from functionalities.base import Base


class CommunicationSession(Base):
    """Represents any user communication handled by the assistant."""

    __tablename__ = "communication_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    session_type = Column(
        String(20), nullable=False, index=True
    )  # call, meeting, chat
    channel = Column(String(50), nullable=True)  # phone, zoom, teams, slack
    external_session_id = Column(String(255), nullable=True, index=True)

    subject = Column(String(255), nullable=True)
    counterpart_name = Column(String(255), nullable=True)
    counterpart_identifier = Column(String(255), nullable=True)  # phone/email/slack id
    counterpart_type = Column(String(50), nullable=True)  # phone, email, handle

    direction = Column(String(20), nullable=True)  # incoming, outgoing, system
    status = Column(
        String(30), default="completed", nullable=False
    )  # completed, missed, cancelled, active

    ai_participated = Column(Boolean, default=False)
    ai_role = Column(String(50), default="delegate")
    disclosure_sent = Column(Boolean, default=False)

    started_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True, index=True)
    duration_seconds = Column(Integer, nullable=True)

    summary_text = Column(Text, nullable=True)
    summary_bullets = Column(JSON, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    topics = Column(JSON, nullable=True)
    action_items = Column(JSON, nullable=True)

    recording_url = Column(String(1024), nullable=True)
    session_metadata = Column(JSON, nullable=True)
    ai_decisions = Column(JSON, nullable=True)

    retention_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __mapper_args__ = {
        "polymorphic_on": session_type,
        "polymorphic_identity": "session",
    }

    participants = relationship(
        "SessionParticipant",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    transcript = relationship(
        "SessionTranscript",
        back_populates="session",
        cascade="all, delete-orphan",
        uselist=False,
    )
    messages = relationship(
        "SessionMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    shared_files = relationship(
        "SharedFileLog",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_type": self.session_type,
            "channel": self.channel,
            "external_session_id": self.external_session_id,
            "subject": self.subject,
            "counterpart_name": self.counterpart_name,
            "counterpart_identifier": self.counterpart_identifier,
            "counterpart_type": self.counterpart_type,
            "direction": self.direction,
            "status": self.status,
            "ai_participated": self.ai_participated,
            "ai_role": self.ai_role,
            "disclosure_sent": self.disclosure_sent,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "summary_text": self.summary_text,
            "summary_bullets": self.summary_bullets or [],
            "sentiment_score": self.sentiment_score,
            "topics": self.topics or [],
            "action_items": self.action_items or [],
            "session_metadata": self.session_metadata or {},
            "ai_decisions": self.ai_decisions or {},
            "retention_expires_at": self.retention_expires_at.isoformat()
            if self.retention_expires_at
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "participants": [participant.to_dict() for participant in self.participants],
            "transcript": self.transcript.to_dict() if self.transcript else None,
        }


class CallSession(CommunicationSession):
    """Single table inheritance marker for phone calls."""

    __mapper_args__ = {"polymorphic_identity": "call"}


class MeetingSession(CommunicationSession):
    """Marker for meeting sessions (Zoom, Teams, etc.)."""

    __mapper_args__ = {"polymorphic_identity": "meeting"}


class ChatSession(CommunicationSession):
    """Marker for asynchronous text based channels."""

    __mapper_args__ = {"polymorphic_identity": "chat"}


class SessionParticipant(Base):
    """Participant in a communication session."""

    __tablename__ = "session_participants"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("communication_sessions.id"), nullable=False)
    participant_type = Column(
        String(30), nullable=False, default="external"
    )  # user, ai, external
    identifier = Column(String(255), nullable=True)  # phone/email/slack id
    display_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)  # host, speaker, attendee
    is_host = Column(Boolean, default=False)
    joined_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)
    participant_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    session = relationship("CommunicationSession", back_populates="participants")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "participant_type": self.participant_type,
            "identifier": self.identifier,
            "display_name": self.display_name,
            "role": self.role,
            "is_host": self.is_host,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
            "metadata": self.participant_metadata or {},
        }


class SessionTranscript(Base):
    """Captured transcript and analytics for a session."""

    __tablename__ = "session_transcripts"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("communication_sessions.id"), nullable=False)
    transcript_text = Column(Text, nullable=False)
    provider = Column(String(100), nullable=True)
    language = Column(String(10), default="en")
    confidence = Column(Float, nullable=True)

    segments = Column(JSON, nullable=True)
    summary_text = Column(Text, nullable=True)
    summary_bullets = Column(JSON, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    topics = Column(JSON, nullable=True)
    action_items = Column(JSON, nullable=True)
    mindmap = Column(JSON, nullable=True)

    analytics = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    session = relationship("CommunicationSession", back_populates="transcript")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "transcript_text": self.transcript_text,
            "provider": self.provider,
            "language": self.language,
            "confidence": self.confidence,
            "segments": self.segments or [],
            "summary_text": self.summary_text,
            "summary_bullets": self.summary_bullets or [],
            "sentiment_score": self.sentiment_score,
            "topics": self.topics or [],
            "action_items": self.action_items or [],
            "mindmap": self.mindmap or {},
            "analytics": self.analytics or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SessionMessage(Base):
    """Individual messages linked to a session (chat or meeting chat)."""

    __tablename__ = "session_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("communication_sessions.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("session_participants.id"), nullable=True)

    direction = Column(String(20), nullable=False, default="incoming")
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")  # text, file, reaction
    message_metadata = Column(JSON, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    is_ai_generated = Column(Boolean, default=False)

    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    session = relationship("CommunicationSession", back_populates="messages")
    participant = relationship("SessionParticipant")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "direction": self.direction,
            "content": self.content,
            "content_type": self.content_type,
            "message_metadata": self.message_metadata or {},
            "sentiment_score": self.sentiment_score,
            "is_ai_generated": self.is_ai_generated,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


class SharedFileLog(Base):
    """Audit record of documents shared during a session."""

    __tablename__ = "shared_files_log"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("communication_sessions.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    recipient_identifier = Column(String(255), nullable=True)
    channel = Column(String(50), nullable=True)
    shared_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    file_metadata = Column("metadata", JSON, nullable=True)

    session = relationship("CommunicationSession", back_populates="shared_files")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "document_id": self.document_id,
            "recipient_identifier": self.recipient_identifier,
            "channel": self.channel,
            "shared_at": self.shared_at.isoformat() if self.shared_at else None,
            "metadata": self.file_metadata or {},
        }


class ActiveSession(Base):
    """Tracks sessions that are currently in progress for orchestration."""

    __tablename__ = "active_sessions"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("communication_sessions.id"), nullable=False)
    adapter = Column(String(50), nullable=False)  # telephony, zoom, teams, slack
    status = Column(String(30), default="joining")  # joining, live, ending
    last_heartbeat = Column(DateTime, default=datetime.utcnow, nullable=False)
    context = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "adapter": self.adapter,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat()
            if self.last_heartbeat
            else None,
            "context": self.context or {},
        }

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

from functionalities.base import Base


class UserIntegration(Base):
    """Stores per-user integration credentials for 3rd party platforms."""

    __tablename__ = "user_integrations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    platform = Column(String(50), nullable=False)  # zoom, teams, slack, telephony
    account_identifier = Column(String(255), nullable=True)
    auth_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    scopes = Column(JSON, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    integration_metadata = Column("metadata", JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "platform": self.platform,
            "account_identifier": self.account_identifier,
            "scopes": self.scopes or [],
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.integration_metadata or {},
            "is_active": self.is_active,
            "last_synced_at": self.last_synced_at.isoformat()
            if self.last_synced_at
            else None,
        }


class DelegationRule(Base):
    """Rules that determine when the assistant should take over."""

    __tablename__ = "delegation_rules"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    channel = Column(String(50), nullable=False)  # phone, zoom, slack
    condition_type = Column(
        String(50), nullable=False
    )  # presence, keyword, schedule, fallback
    condition_payload = Column(JSON, nullable=True)
    action = Column(String(50), nullable=False)  # auto_join, notify, ignore
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "channel": self.channel,
            "condition_type": self.condition_type,
            "condition_payload": self.condition_payload or {},
            "action": self.action,
            "is_active": self.is_active,
        }


class MeetingSchedule(Base):
    """Cache of meetings the assistant may need to join."""

    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    platform = Column(String(50), nullable=False)
    meeting_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    join_url = Column(String(1024), nullable=True)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=True)
    ai_delegate = Column(Boolean, default=False)

    meeting_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "platform": self.platform,
            "meeting_id": self.meeting_id,
            "title": self.title,
            "join_url": self.join_url,
            "scheduled_start": self.scheduled_start.isoformat()
            if self.scheduled_start
            else None,
            "scheduled_end": self.scheduled_end.isoformat()
            if self.scheduled_end
            else None,
            "ai_delegate": self.ai_delegate,
            "metadata": self.meeting_metadata or {},
        }

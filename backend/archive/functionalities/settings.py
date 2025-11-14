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
)

from functionalities.base import Base


class UserSettings(Base):
    """Aggregated user preferences for the assistant across channels."""

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    ai_mode_enabled = Column(Boolean, default=False)
    auto_join_meetings = Column(Boolean, default=False)
    auto_reply_chats = Column(Boolean, default=False)
    voice_clone_enabled = Column(Boolean, default=False)
    disclose_voice_clone = Column(Boolean, default=True)

    data_retention_days = Column(Integer, default=30)
    transcript_auto_delete_days = Column(Integer, default=90)

    preferred_voice_model_id = Column(Integer, ForeignKey("voice_models.id"), nullable=True)

    spam_filter_level = Column(String(20), default="medium")
    important_contacts_policy = Column(String(20), default="notify")

    notification_channels = Column(JSON, nullable=True)
    feature_toggles = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "ai_mode_enabled": self.ai_mode_enabled,
            "auto_join_meetings": self.auto_join_meetings,
            "auto_reply_chats": self.auto_reply_chats,
            "voice_clone_enabled": self.voice_clone_enabled,
            "disclose_voice_clone": self.disclose_voice_clone,
            "data_retention_days": self.data_retention_days,
            "transcript_auto_delete_days": self.transcript_auto_delete_days,
            "preferred_voice_model_id": self.preferred_voice_model_id,
            "spam_filter_level": self.spam_filter_level,
            "important_contacts_policy": self.important_contacts_policy,
            "notification_channels": self.notification_channels or [],
            "feature_toggles": self.feature_toggles or {},
        }


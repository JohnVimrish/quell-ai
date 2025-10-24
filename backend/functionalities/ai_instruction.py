from datetime import datetime, timedelta

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
from sqlalchemy.sql import func

from functionalities.base import Base


class AIInstruction(Base):
    __tablename__ = "ai_instructions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    instruction_text = Column(Text, nullable=False)

    instruction_type = Column(String(50), default="general")
    context_type = Column(String(20), default="all")  # call, meeting, chat, all
    channel = Column(String(50), nullable=True)  # zoom, teams, slack, phone
    target_identifier = Column(String(255), nullable=True)  # contact or meeting id
    context_tags = Column(JSON, nullable=True)

    priority = Column(String(10), default="normal")
    priority_weight = Column(Integer, default=0)
    status = Column(String(20), default="active")

    verification_required = Column(Boolean, default=False)
    verification_method = Column(String(50), nullable=True)
    verification_data = Column(JSON, nullable=True)

    usage_count = Column(Integer, default=0)
    max_usage = Column(Integer, nullable=True)
    last_triggered_at = Column(DateTime, nullable=True)

    expires_at = Column(DateTime, nullable=True)
    auto_archive_at = Column(DateTime, nullable=True)

    completed_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    applies_to_documents = Column(Boolean, default=False)
    escalation_policy = Column(String(50), nullable=True)
    follow_up_action = Column(JSON, nullable=True)

    def is_active(self) -> bool:
        now = datetime.utcnow()
        if self.status != "active":
            return False
        if self.expires_at and now > self.expires_at:
            return False
        if self.auto_archive_at and now > self.auto_archive_at:
            return False
        if self.max_usage and self.usage_count >= self.max_usage:
            return False
        return True

    def mark_used(self) -> None:
        self.usage_count += 1
        self.last_triggered_at = datetime.utcnow()
        if self.max_usage and self.usage_count >= self.max_usage:
            self.status = "completed"
            self.completed_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "instruction_text": self.instruction_text,
            "instruction_type": self.instruction_type,
            "context_type": self.context_type,
            "channel": self.channel,
            "target_identifier": self.target_identifier,
            "context_tags": self.context_tags or [],
            "priority": self.priority,
            "priority_weight": self.priority_weight,
            "status": self.status,
            "verification_required": self.verification_required,
            "verification_method": self.verification_method,
            "usage_count": self.usage_count,
            "max_usage": self.max_usage,
            "last_triggered_at": self.last_triggered_at.isoformat()
            if self.last_triggered_at
            else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "auto_archive_at": self.auto_archive_at.isoformat()
            if self.auto_archive_at
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active(),
            "applies_to_documents": self.applies_to_documents,
            "escalation_policy": self.escalation_policy,
            "follow_up_action": self.follow_up_action or {},
        }

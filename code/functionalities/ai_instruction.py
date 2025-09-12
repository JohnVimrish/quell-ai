from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime, timedelta

Base = declarative_base()

class AIInstruction(Base):
    __tablename__ = 'ai_instructions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(200), nullable=False)
    instruction_text = Column(Text, nullable=False)
    instruction_type = Column(String(50), default='general')  # 'call', 'text', 'general', 'verification'
    priority = Column(String(10), default='normal')  # 'low', 'normal', 'high'
    status = Column(String(20), default='active')  # 'active', 'completed', 'archived', 'expired'
    target_contact = Column(String(100), nullable=True)  # Specific contact this applies to
    verification_required = Column(Boolean, default=False)
    verification_method = Column(String(50), nullable=True)  # 'passcode', 'question', 'callback'
    verification_data = Column(JSON, nullable=True)  # Store passcode/question data
    usage_count = Column(Integer, default=0)
    max_usage = Column(Integer, nullable=True)  # Limit how many times this can be used
    expires_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def is_active(self):
        now = datetime.utcnow()
        if self.status != 'active':
            return False
        if self.expires_at and now > self.expires_at:
            return False
        if self.max_usage and self.usage_count >= self.max_usage:
            return False
        return True
    
    def mark_used(self):
        self.usage_count += 1
        if self.max_usage and self.usage_count >= self.max_usage:
            self.status = 'completed'
            self.completed_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'instruction_text': self.instruction_text,
            'instruction_type': self.instruction_type,
            'priority': self.priority,
            'status': self.status,
            'target_contact': self.target_contact,
            'verification_required': self.verification_required,
            'verification_method': self.verification_method,
            'usage_count': self.usage_count,
            'max_usage': self.max_usage,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active()
        }
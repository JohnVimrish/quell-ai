from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class Call(Base):
    __tablename__ = 'calls'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=True)
    caller_number = Column(String(20), nullable=False)
    caller_name = Column(String(100), nullable=True)
    direction = Column(String(10), nullable=False)  # 'inbound', 'outbound'
    status = Column(String(20), nullable=False)  # 'answered_ai', 'answered_user', 'missed', 'blocked'
    category = Column(String(20), default='routine')  # 'important', 'spam', 'routine'
    duration_seconds = Column(Integer, default=0)
    ai_handled = Column(Boolean, default=False)
    recording_url = Column(String(500), nullable=True)
    spam_score = Column(Integer, default=0)
    trust_score = Column(Integer, default=50)
    caller_satisfaction = Column(Integer, nullable=True)  # 1-5 rating if available
    escalated_to_user = Column(Boolean, default=False)
    call_summary = Column(Text, nullable=True)
    mind_map_data = Column(Text, nullable=True)  # JSON string
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    contact = relationship("Contact")
    transcript = relationship("CallTranscript", back_populates="call", uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'caller_number': self.caller_number,
            'caller_name': self.caller_name,
            'direction': self.direction,
            'status': self.status,
            'category': self.category,
            'duration_seconds': self.duration_seconds,
            'ai_handled': self.ai_handled,
            'recording_url': self.recording_url,
            'spam_score': self.spam_score,
            'trust_score': self.trust_score,
            'caller_satisfaction': self.caller_satisfaction,
            'escalated_to_user': self.escalated_to_user,
            'call_summary': self.call_summary,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'contact': self.contact.to_dict() if self.contact else None
        }

class CallTranscript(Base):
    __tablename__ = 'call_transcripts'
    
    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, ForeignKey('calls.id'), nullable=False)
    transcript_text = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.0)  # Speech-to-text confidence
    language_detected = Column(String(10), default='en')
    processing_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    call = relationship("Call", back_populates="transcript")
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'transcript_text': self.transcript_text,
            'confidence_score': self.confidence_score,
            'language_detected': self.language_detected,
            'processing_time_ms': self.processing_time_ms,
            'created_at': self.created_at.isoformat()
        }
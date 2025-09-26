
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True)
    ai_mode_enabled = Column(Boolean, default=False)
    ai_mode_calls = Column(Boolean, default=True)
    ai_mode_texts = Column(Boolean, default=True)
    ai_mode_until = Column(DateTime, nullable=True)
    voice_model_trained = Column(Boolean, default=False)
    spam_threshold = Column(Integer, default=70)  # 0-100 spam score threshold
    call_recording_enabled = Column(Boolean, default=False)
    data_retention_days = Column(Integer, default=30)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone_number': self.phone_number,
            'ai_mode_enabled': self.ai_mode_enabled,
            'ai_mode_calls': self.ai_mode_calls,
            'ai_mode_texts': self.ai_mode_texts,
            'ai_mode_until': self.ai_mode_until.isoformat() if self.ai_mode_until else None,
            'voice_model_trained': self.voice_model_trained,
            'spam_threshold': self.spam_threshold,
            'call_recording_enabled': self.call_recording_enabled,
            'data_retention_days': self.data_retention_days
        }
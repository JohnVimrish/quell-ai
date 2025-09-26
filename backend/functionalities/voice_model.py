from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class VoiceModel(Base):
    __tablename__ = 'voice_models'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), default='1.0')
    model_path = Column(String(500), nullable=False)
    training_status = Column(String(20), default='pending')  # 'pending', 'training', 'completed', 'failed'
    training_progress = Column(Float, default=0.0)  # 0.0 to 100.0
    quality_score = Column(Float, nullable=True)  # Voice similarity score
    sample_count = Column(Integer, default=0)
    training_duration_minutes = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'training_status': self.training_status,
            'training_progress': self.training_progress,
            'quality_score': self.quality_score,
            'sample_count': self.sample_count,
            'training_duration_minutes': self.training_duration_minutes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class VoiceSample(Base):
    __tablename__ = 'voice_samples'
    
    id = Column(Integer, primary_key=True)
    voice_model_id = Column(Integer, ForeignKey('voice_models.id'), nullable=False)
    sample_text = Column(Text, nullable=False)
    audio_file_path = Column(String(500), nullable=False)
    duration_seconds = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=True)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
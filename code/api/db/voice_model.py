from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship

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
    total_audio_duration = Column(Float, default=0.0)  # Total seconds of training audio
    is_active = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)  # Admin approval for voice cloning
    voice_profile = Column(JSON, nullable=True)  # Stored voice characteristics
    training_config = Column(JSON, nullable=True)  # Training parameters used
    error_message = Column(Text, nullable=True)
    disclosure_text = Column(Text, nullable=True)  # Custom disclosure message
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    samples = relationship("VoiceSample", back_populates="voice_model", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'model_path': self.model_path,
            'training_status': self.training_status,
            'training_progress': self.training_progress,
            'quality_score': self.quality_score,
            'sample_count': self.sample_count,
            'training_duration_minutes': self.training_duration_minutes,
            'total_audio_duration': self.total_audio_duration,
            'is_active': self.is_active,
            'is_approved': self.is_approved,
            'voice_profile': self.voice_profile,
            'training_config': self.training_config,
            'error_message': self.error_message,
            'disclosure_text': self.disclosure_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'usage_count': self.usage_count
        }
    
    def update_progress(self, progress: float, status: str = None):
        """Update training progress"""
        self.training_progress = min(max(progress, 0.0), 100.0)
        if status:
            self.training_status = status
    
    def mark_completed(self, quality_score: float = None):
        """Mark training as completed"""
        self.training_status = 'completed'
        self.training_progress = 100.0
        self.completed_at = func.now()
        if quality_score:
            self.quality_score = quality_score
    
    def mark_failed(self, error_message: str):
        """Mark training as failed"""
        self.training_status = 'failed'
        self.error_message = error_message
    
    def activate(self):
        """Activate this voice model"""
        self.is_active = True
        self.last_used_at = func.now()
    
    def deactivate(self):
        """Deactivate this voice model"""
        self.is_active = False
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count += 1
        self.last_used_at = func.now()

class VoiceSample(Base):
    __tablename__ = 'voice_samples'
    
    id = Column(Integer, primary_key=True)
    voice_model_id = Column(Integer, ForeignKey('voice_models.id'), nullable=False)
    sample_text = Column(Text, nullable=False)
    audio_file_path = Column(String(500), nullable=False)
    duration_seconds = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=True)
    is_approved = Column(Boolean, default=True)
    voice_features = Column(JSON, nullable=True)  # Extracted voice features
    processing_status = Column(String(20), default='pending')  # 'pending', 'processed', 'failed'
    error_message = Column(Text, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    sample_rate = Column(Integer, default=22050)
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    voice_model = relationship("VoiceModel", back_populates="samples")
    
    def to_dict(self):
        return {
            'id': self.id,
            'voice_model_id': self.voice_model_id,
            'sample_text': self.sample_text,
            'audio_file_path': self.audio_file_path,
            'duration_seconds': self.duration_seconds,
            'quality_score': self.quality_score,
            'is_approved': self.is_approved,
            'voice_features': self.voice_features,
            'processing_status': self.processing_status,
            'error_message': self.error_message,
            'file_size_bytes': self.file_size_bytes,
            'sample_rate': self.sample_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    def mark_processed(self, features: dict = None, quality_score: float = None):
        """Mark sample as processed"""
        self.processing_status = 'processed'
        self.processed_at = func.now()
        if features:
            self.voice_features = features
        if quality_score:
            self.quality_score = quality_score
    
    def mark_failed(self, error_message: str):
        """Mark sample processing as failed"""
        self.processing_status = 'failed'
        self.error_message = error_message

class VoiceGeneration(Base):
    __tablename__ = 'voice_generations'
    
    id = Column(Integer, primary_key=True)
    voice_model_id = Column(Integer, ForeignKey('voice_models.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    input_text = Column(Text, nullable=False)
    output_file_path = Column(String(500), nullable=True)
    generation_status = Column(String(20), default='pending')  # 'pending', 'generating', 'completed', 'failed'
    duration_seconds = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    quality_score = Column(Float, nullable=True)
    disclosure_shown = Column(Boolean, default=False)  # Whether AI disclosure was shown
    disclosure_acknowledged = Column(Boolean, default=False)  # Whether user acknowledged
    error_message = Column(Text, nullable=True)
    generation_params = Column(JSON, nullable=True)  # Parameters used for generation
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'voice_model_id': self.voice_model_id,
            'user_id': self.user_id,
            'input_text': self.input_text,
            'output_file_path': self.output_file_path,
            'generation_status': self.generation_status,
            'duration_seconds': self.duration_seconds,
            'file_size_bytes': self.file_size_bytes,
            'quality_score': self.quality_score,
            'disclosure_shown': self.disclosure_shown,
            'disclosure_acknowledged': self.disclosure_acknowledged,
            'error_message': self.error_message,
            'generation_params': self.generation_params,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
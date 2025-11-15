from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class DocumentEmbedding(Base):
    __tablename__ = 'data_feeds_vectors.embeddings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    document_type = Column(String(50), nullable=False)  # 'instruction', 'call_transcript', 'text_message', 'contact_info'
    document_id = Column(Integer, nullable=True)  # Reference to original document
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384))  # 384-dimensional embeddings
    document_metadata = Column(JSON, nullable=True)
    relevance_score = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_type': self.document_type,
            'document_id': self.document_id,
            'content': self.content,
            'document_metadata': self.document_metadata,
            'relevance_score': self.relevance_score,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat()
        }

class ConversationContext(Base):
    __tablename__ = 'conversation_contexts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    conversation_id = Column(String(100), nullable=False)  # Unique conversation identifier
    conversation_type = Column(String(20), nullable=False)  # 'call', 'text'
    context_data = Column(JSON, nullable=False)  # Store conversation state
    embedding = Column(Vector(384))  # Context embedding for similarity matching
    entities_extracted = Column(JSON, nullable=True)  # Named entities, intents, etc.
    sentiment_score = Column(Float, default=0.0)
    urgency_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

class SpamPattern(Base):
    __tablename__ = 'spam_patterns'
    
    id = Column(Integer, primary_key=True)
    pattern_type = Column(String(50), nullable=False)  # 'text', 'phone', 'behavior'
    pattern_data = Column(Text, nullable=False)
    embedding = Column(Vector(384))
    confidence_score = Column(Float, nullable=False)
    detection_count = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)
    accuracy_rate = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class MLModelMetrics(Base):
    __tablename__ = 'ml_model_metrics'
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20), nullable=False)
    metric_type = Column(String(50), nullable=False)  # 'accuracy', 'precision', 'recall', 'f1'
    metric_value = Column(Float, nullable=False)
    dataset_size = Column(Integer, nullable=False)
    training_time_seconds = Column(Float, nullable=True)
    model_parameters = Column(JSON, nullable=True)
    accuracy = Column(Float, default=0.0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    training_samples = Column(Integer, default=0)
    last_trained = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
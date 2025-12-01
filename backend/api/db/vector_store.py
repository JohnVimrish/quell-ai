from typing import Any, Dict

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Text, Float, JSON, Boolean
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
    content = Column("content_snippet", Text, nullable=False)
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


class ConversationLabIngest(Base):
    __tablename__ = 'conversation_lab_ingests'
    __table_args__ = {"schema": "ai_intelligence"}

    id = Column(BigInteger, primary_key=True)
    session_id = Column(String(128), nullable=True)
    user_id = Column(BigInteger, nullable=False)
    filename = Column(Text, nullable=False)
    file_type = Column(String(16), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    storage_path = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="queued")
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    embedding_id = Column(BigInteger, nullable=True)
    needs_embedding = Column(Boolean, default=True)
    attempts = Column(Integer, default=0)
    queued_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    ingest_metadata = Column("metadata", JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "embedding_id": self.embedding_id,
            "needs_embedding": self.needs_embedding,
            "attempts": self.attempts,
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "metadata": self.ingest_metadata or {},
        }


class ConversationLabMemory(Base):
    __tablename__ = "conversation_lab_memories"
    __table_args__ = {"schema": "ai_intelligence"}

    id = Column(BigInteger, primary_key=True)
    source_user_id = Column(BigInteger, nullable=True)
    source_session_id = Column(String(128), nullable=True)
    source_display_name = Column(String(255), nullable=True)
    target_name = Column(Text, nullable=False)
    memory_text = Column(Text, nullable=False)
    instruction_scope = Column(String(64), nullable=False, default="remind-on-interaction")
    delivered = Column(Boolean, nullable=False, default=False)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_user_id": self.source_user_id,
            "source_session_id": self.source_session_id,
            "source_display_name": self.source_display_name,
            "target_name": self.target_name,
            "memory_text": self.memory_text,
            "instruction_scope": self.instruction_scope,
            "delivered": self.delivered,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

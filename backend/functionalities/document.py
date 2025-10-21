from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from functionalities.base import Base


class Document(Base):
    """Stores metadata and policy flags for documents the AI may reference."""

    __tablename__ = "documents"
    __table_args__ = {"schema": "data_feeds"}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_management.users.id"), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    storage_uri = Column(String(1024), nullable=False)  # path or cloud url
    storage_type = Column(String(50), default="local")

    classification = Column(String(50), default="internal")  # public/internal/confidential
    sensitivity_level = Column(String(50), default="normal")

    tags = Column(JSON, nullable=True)
    allowed_recipients = Column(JSON, nullable=True)  # e.g. domains, emails, roles
    allowed_contexts = Column(JSON, nullable=True)  # meeting/chat keywords
    blocked_contexts = Column(JSON, nullable=True)

    shareable = Column(Boolean, default=False)
    allow_ai_to_suggest = Column(Boolean, default=False)
    max_share_count = Column(Integer, nullable=True)
    share_count = Column(Integer, default=0)

    retention_days = Column(Integer, default=90)
    retention_expires_at = Column(DateTime, nullable=True)

    # Data feed specific fields
    file_size_bytes = Column(BigInteger, nullable=True)
    file_type = Column(String(50), nullable=True)  # txt, csv, xlsx, text_input
    original_content = Column(Text, nullable=True)
    processed_content = Column(Text, nullable=True)
    content_metadata = Column(JSON, default=dict, nullable=True)
    embedding = Column(Vector(384), nullable=True)
    vector_metadata = Column(JSON, default=dict, nullable=True)
    ollama_model = Column(String(100), nullable=True)

    # Version control (Phase 2)
    version = Column(Integer, default=1, nullable=False)
    previous_embedding = Column(Vector(384), nullable=True)
    last_modified_at = Column(DateTime, nullable=True)
    embedding_changed = Column(Boolean, default=False, nullable=False)

    # Soft deletion (Phase 2)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("user_management.users.id"), nullable=True)

    last_shared_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    rules = relationship(
        "DocumentAccessRule",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "storage_uri": self.storage_uri,
            "storage_type": self.storage_type,
            "classification": self.classification,
            "sensitivity_level": self.sensitivity_level,
            "tags": self.tags or [],
            "allowed_recipients": self.allowed_recipients or [],
            "allowed_contexts": self.allowed_contexts or [],
            "blocked_contexts": self.blocked_contexts or [],
            "shareable": self.shareable,
            "allow_ai_to_suggest": self.allow_ai_to_suggest,
            "max_share_count": self.max_share_count,
            "share_count": self.share_count,
            "retention_days": self.retention_days,
            "retention_expires_at": self.retention_expires_at.isoformat()
            if self.retention_expires_at
            else None,
            "file_size_bytes": self.file_size_bytes,
            "file_type": self.file_type,
            "content_metadata": self.content_metadata or {},
            "vector_metadata": self.vector_metadata or {},
            "ollama_model": self.ollama_model,
            "has_embedding": self.embedding is not None,
            "version": self.version,
            "last_modified_at": self.last_modified_at.isoformat()
            if self.last_modified_at
            else None,
            "embedding_changed": self.embedding_changed,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": self.deleted_by,
            "last_shared_at": self.last_shared_at.isoformat()
            if self.last_shared_at
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DocumentAccessRule(Base):
    """Fine-grained rule describing when a document can be shared."""

    __tablename__ = "document_access_rules"
    __table_args__ = {"schema": "data_feeds"}

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("data_feeds.documents.id"), nullable=False)

    rule_type = Column(String(50), nullable=False)  # recipient|context|time|instruction
    match_expression = Column(String(512), nullable=False)
    allow = Column(Boolean, default=True)
    rule_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    document = relationship("Document", back_populates="rules")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "rule_type": self.rule_type,
            "match_expression": self.match_expression,
            "allow": self.allow,
            "metadata": self.rule_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InstructionDocumentLink(Base):
    """Associates instruction entries with documents for quick access."""

    __tablename__ = "instruction_document_links"
    __table_args__ = {"schema": "data_feeds"}

    id = Column(Integer, primary_key=True)
    instruction_id = Column(Integer, ForeignKey("ai_instructions.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("data_feeds.documents.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DocumentVersion(Base):
    """Historical versions of documents for audit and recovery."""

    __tablename__ = "document_versions"
    __table_args__ = {"schema": "data_feeds"}

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("data_feeds.documents.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=True)
    content_snapshot = Column(Text, nullable=True)
    metadata_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("user_management.users.id"), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "version": self.version,
            "content_snapshot": self.content_snapshot,
            "metadata_snapshot": self.metadata_snapshot or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }


class DocumentDeletionLog(Base):
    """Audit log of document deletions with metadata snapshots."""

    __tablename__ = "document_deletion_log"
    __table_args__ = {"schema": "data_feeds"}

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("data_feeds.documents.id"), nullable=False)
    document_name = Column(Text, nullable=False)
    deleted_by = Column(Integer, ForeignKey("user_management.users.id"), nullable=True)
    deleted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(Text, nullable=True)
    vector_metadata_snapshot = Column(JSON, nullable=True)
    file_type = Column(String(50), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "deleted_by": self.deleted_by,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "reason": self.reason,
            "vector_metadata_snapshot": self.vector_metadata_snapshot or {},
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
        }

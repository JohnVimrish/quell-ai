from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from functionalities.document import (
    Document,
    DocumentAccessRule,
    DocumentVersion,
    DocumentDeletionLog,
)
from functionalities.communication_session import SharedFileLog


class DocumentsRepository:
    """Repository for managing sharable documents and policies."""

    def __init__(
        self,
        database_url: str,
        _queries_config: Optional[Dict] = None,
        query_manager: Optional[Any] = None
    ):
        self._engine = create_engine(database_url, future=True)
        self._session_factory = sessionmaker(
            bind=self._engine, autoflush=False, expire_on_commit=False
        )
        self.query_manager = query_manager

    @contextmanager
    def _session_scope(self) -> Session:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_documents(self, user_id: int) -> List[Dict]:
        with self._session_scope() as sess:
            docs = (
                sess.query(Document)
                .filter(
                    Document.user_id == user_id,
                    Document.is_deleted == False  # noqa: E712
                )
                .all()
            )
            return [doc.to_dict() for doc in docs]

    def get_document(self, document_id: int, user_id: int) -> Optional[Dict]:
        with self._session_scope() as sess:
            doc = (
                sess.query(Document)
                .filter(Document.id == document_id, Document.user_id == user_id)
                .first()
            )
            return doc.to_dict() if doc else None

    def create_document(self, payload: Dict) -> Optional[int]:
        document = Document(
            user_id=payload["user_id"],
            name=payload["name"],
            description=payload.get("description"),
            storage_uri=payload["storage_uri"],
            storage_type=payload.get("storage_type", "local"),
            classification=payload.get("classification", "internal"),
            sensitivity_level=payload.get("sensitivity_level", "normal"),
            tags=payload.get("tags"),
            allowed_recipients=payload.get("allowed_recipients"),
            allowed_contexts=payload.get("allowed_contexts"),
            blocked_contexts=payload.get("blocked_contexts"),
            shareable=payload.get("shareable", False),
            allow_ai_to_suggest=payload.get("allow_ai_to_suggest", False),
            max_share_count=payload.get("max_share_count"),
            retention_days=payload.get("retention_days", 90),
            retention_expires_at=payload.get("retention_expires_at"),
        )
        with self._session_scope() as sess:
            sess.add(document)
            sess.flush()

            for rule in payload.get("rules", []):
                sess.add(
                    DocumentAccessRule(
                        document_id=document.id,
                        rule_type=rule["rule_type"],
                        match_expression=rule["match_expression"],
                        allow=rule.get("allow", True),
                        rule_metadata=rule.get("metadata"),
                    )
                )
            return document.id

    def update_document(self, document_id: int, user_id: int, payload: Dict) -> bool:
        with self._session_scope() as sess:
            doc = (
                sess.query(Document)
                .filter(Document.id == document_id, Document.user_id == user_id)
                .first()
            )
            if not doc:
                return False

            for key, value in payload.items():
                if hasattr(doc, key):
                    setattr(doc, key, value)

            # Optionally replace rules
            if "rules" in payload:
                sess.query(DocumentAccessRule).filter(
                    DocumentAccessRule.document_id == document_id
                ).delete(synchronize_session=False)
                for rule in payload["rules"]:
                    sess.add(
                        DocumentAccessRule(
                            document_id=document_id,
                            rule_type=rule["rule_type"],
                            match_expression=rule["match_expression"],
                            allow=rule.get("allow", True),
                            rule_metadata=rule.get("metadata"),
                        )
                    )
            return True

    def delete_document(self, document_id: int, user_id: int) -> bool:
        with self._session_scope() as sess:
            doc = (
                sess.query(Document)
                .filter(Document.id == document_id, Document.user_id == user_id)
                .first()
            )
            if not doc:
                return False
            sess.delete(doc)
            return True

    def record_share(
        self,
        session_id: int,
        document_id: int,
        recipient_identifier: Optional[str],
        channel: Optional[str],
        metadata: Optional[Dict] = None,
    ) -> int:
        log_entry = SharedFileLog(
            session_id=session_id,
            document_id=document_id,
            recipient_identifier=recipient_identifier,
            channel=channel,
            shared_at=datetime.utcnow(),
            file_metadata=metadata,
        )
        with self._session_scope() as sess:
            sess.add(log_entry)
            sess.flush()
            document = sess.get(Document, document_id)
            if document:
                document.share_count = (document.share_count or 0) + 1
                document.last_shared_at = datetime.utcnow()
            return log_entry.id

    def create_data_feed(self, payload: Dict[str, Any]) -> Optional[int]:
        """
        Create a new data feed document with processed content.
        
        Args:
            payload: Dictionary containing all document fields including:
                - user_id, name, file_type, file_size_bytes
                - original_content, processed_content
                - content_metadata, vector_metadata
                - embedding, ollama_model
                
        Returns:
            Document ID if successful, None otherwise
        """
        document = Document(
            user_id=payload["user_id"],
            name=payload["name"],
            description=payload.get("description"),
            storage_uri=payload.get("storage_uri", ""),
            storage_type=payload.get("storage_type", "local"),
            classification=payload.get("classification", "internal"),
            sensitivity_level=payload.get("sensitivity_level", "normal"),
            tags=payload.get("tags"),
            shareable=payload.get("shareable", False),
            allow_ai_to_suggest=payload.get("allow_ai_to_suggest", True),
            # Data feed specific fields
            file_type=payload.get("file_type"),
            file_size_bytes=payload.get("file_size_bytes"),
            original_content=payload.get("original_content"),
            processed_content=payload.get("processed_content"),
            content_metadata=payload.get("content_metadata", {}),
            embedding=payload.get("embedding"),
            vector_metadata=payload.get("vector_metadata", {}),
            ollama_model=payload.get("ollama_model"),
        )
        
        with self._session_scope() as sess:
            sess.add(document)
            sess.flush()
            return document.id

    def search_by_vector(
        self,
        query_embedding: List[float],
        user_id: int,
        limit: int = 5,
        file_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search documents using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            user_id: User ID for filtering
            limit: Maximum number of results
            file_types: Optional list of file types to filter by
            
        Returns:
            List of matching documents with similarity scores
        """
        with self._session_scope() as sess:
            try:
                # Build filter conditions
                type_filter = ""
                params: Dict[str, Any] = {
                    "query_embedding": query_embedding,
                    "user_id": user_id,
                    "limit": limit,
                }
                
                if file_types:
                    type_filter = "AND file_type = ANY(:file_types)"
                    params["file_types"] = file_types
                
                # Vector similarity search
                sql_query = text(
                    f"""
                    SELECT id, name, description, file_type, file_size_bytes,
                           content_metadata, vector_metadata, created_at,
                           1 - (embedding <=> :query_embedding) AS similarity_score
                    FROM data_feeds.documents
                    WHERE user_id = :user_id 
                      AND embedding IS NOT NULL
                      AND is_deleted = false
                      {type_filter}
                    ORDER BY embedding <=> :query_embedding
                    LIMIT :limit
                    """
                )
                
                result = sess.execute(sql_query, params)
                rows = result.fetchall()
                
                documents = []
                for row in rows:
                    documents.append({
                        "id": row.id,
                        "name": row.name,
                        "description": row.description,
                        "file_type": row.file_type,
                        "file_size_bytes": row.file_size_bytes,
                        "content_metadata": row.content_metadata or {},
                        "vector_metadata": row.vector_metadata or {},
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "similarity_score": float(row.similarity_score),
                    })
                
                return documents
                
            except Exception:
                # If vector search fails, return empty list
                return []

    def get_relevant_content(self, document_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve document content for AI response generation.
        
        Args:
            document_id: Document ID
            user_id: User ID for access control
            
        Returns:
            Dictionary with document content and metadata
        """
        with self._session_scope() as sess:
            doc = (
                sess.query(Document)
                .filter(Document.id == document_id, Document.user_id == user_id)
                .first()
            )
            
            if not doc:
                return None
            
            return {
                "id": doc.id,
                "name": doc.name,
                "file_type": doc.file_type,
                "processed_content": doc.processed_content,
                "original_content": doc.original_content,
                "content_metadata": doc.content_metadata or {},
                "vector_metadata": doc.vector_metadata or {},
            }

    # ===== Phase 2: Version Control Methods =====

    def check_existing_document(
        self,
        name: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a document with the given name already exists.
        
        Args:
            name: Document name
            user_id: User ID
            
        Returns:
            Dictionary with document info if exists, None otherwise
        """
        with self._session_scope() as sess:
            doc = (
                sess.query(Document)
                .filter(
                    Document.name == name,
                    Document.user_id == user_id,
                    Document.is_deleted == False  # noqa: E712
                )
                .first()
            )
            
            if not doc:
                return None
            
            return {
                "id": doc.id,
                "name": doc.name,
                "embedding": doc.embedding,
                "version": doc.version,
                "file_size_bytes": doc.file_size_bytes,
                "content_metadata": doc.content_metadata or {},
            }

    def create_version_snapshot(
        self,
        document_id: int,
        version: int,
        embedding: Optional[List[float]],
        content_snapshot: str,
        metadata_snapshot: Dict[str, Any],
        user_id: int
    ) -> Optional[int]:
        """
        Create a version snapshot for audit and recovery.
        
        Args:
            document_id: Document ID
            version: Version number
            embedding: Embedding vector
            content_snapshot: Content at this version
            metadata_snapshot: Metadata at this version
            user_id: User who created this version
            
        Returns:
            Version snapshot ID if successful
        """
        version_record = DocumentVersion(
            document_id=document_id,
            version=version,
            embedding=embedding,
            content_snapshot=content_snapshot,
            metadata_snapshot=metadata_snapshot,
            created_by=user_id
        )
        
        with self._session_scope() as sess:
            sess.add(version_record)
            sess.flush()
            return version_record.id

    def get_version_history(
        self,
        document_id: int,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get version history for a document.
        
        Args:
            document_id: Document ID
            user_id: User ID for access control
            
        Returns:
            List of version records
        """
        with self._session_scope() as sess:
            # Verify user owns the document
            doc = (
                sess.query(Document)
                .filter(Document.id == document_id, Document.user_id == user_id)
                .first()
            )
            
            if not doc:
                return []
            
            versions = (
                sess.query(DocumentVersion)
                .filter(DocumentVersion.document_id == document_id)
                .order_by(DocumentVersion.version.desc())
                .all()
            )
            
            return [v.to_dict() for v in versions]

    def get_version_content(
        self,
        document_id: int,
        version: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get content of a specific version.
        
        Args:
            document_id: Document ID
            version: Version number
            user_id: User ID for access control
            
        Returns:
            Version content if found
        """
        with self._session_scope() as sess:
            # Verify user owns the document
            doc = (
                sess.query(Document)
                .filter(Document.id == document_id, Document.user_id == user_id)
                .first()
            )
            
            if not doc:
                return None
            
            version_record = (
                sess.query(DocumentVersion)
                .filter(
                    DocumentVersion.document_id == document_id,
                    DocumentVersion.version == version
                )
                .first()
            )
            
            if not version_record:
                return None
            
            return version_record.to_dict()

    def update_document_version(
        self,
        document_id: int,
        embedding: List[float],
        processed_content: str,
        content_metadata: Dict[str, Any],
        vector_metadata: Dict[str, Any],
        embedding_changed: bool
    ) -> Optional[int]:
        """
        Update document with new version, incrementing version number.
        
        Args:
            document_id: Document ID
            embedding: New embedding
            processed_content: New content
            content_metadata: New metadata
            vector_metadata: New vector metadata
            embedding_changed: Whether embedding changed significantly
            
        Returns:
            New version number if successful
        """
        with self._session_scope() as sess:
            doc = sess.query(Document).filter(Document.id == document_id).first()
            
            if not doc:
                return None
            
            # Save previous embedding
            doc.previous_embedding = doc.embedding
            
            # Update with new data
            doc.embedding = embedding
            doc.processed_content = processed_content
            doc.content_metadata = content_metadata
            doc.vector_metadata = vector_metadata
            doc.embedding_changed = embedding_changed
            doc.last_modified_at = datetime.utcnow()
            doc.version += 1
            
            sess.flush()
            return doc.version

    # ===== Phase 2: Soft Deletion Methods =====

    def soft_delete_document(
        self,
        document_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        Soft delete a document (mark as deleted, keep data).
        
        Args:
            document_id: Document ID
            user_id: User ID
            reason: Optional reason for deletion
            
        Returns:
            True if successful, False otherwise
        """
        with self._session_scope() as sess:
            doc = (
                sess.query(Document)
                .filter(Document.id == document_id, Document.user_id == user_id)
                .first()
            )
            
            if not doc:
                return False
            
            # Save metadata snapshot before clearing
            vector_metadata_snapshot = doc.vector_metadata or {}
            
            # Log the deletion
            log_entry = DocumentDeletionLog(
                document_id=document_id,
                document_name=doc.name,
                deleted_by=user_id,
                reason=reason,
                vector_metadata_snapshot=vector_metadata_snapshot,
                file_type=doc.file_type,
                file_size_bytes=doc.file_size_bytes
            )
            sess.add(log_entry)
            
            # Soft delete the document
            doc.is_deleted = True
            doc.deleted_at = datetime.utcnow()
            doc.deleted_by = user_id
            doc.vector_metadata = {}  # Clear metadata
            
            return True

    def restore_document(
        self,
        document_id: int,
        user_id: int
    ) -> bool:
        """
        Restore a soft-deleted document.
        
        Args:
            document_id: Document ID
            user_id: User ID for access control
            
        Returns:
            True if successful, False otherwise
        """
        with self._session_scope() as sess:
            doc = (
                sess.query(Document)
                .filter(
                    Document.id == document_id,
                    Document.user_id == user_id,
                    Document.is_deleted == True  # noqa: E712
                )
                .first()
            )
            
            if not doc:
                return False
            
            # Restore the document
            doc.is_deleted = False
            doc.deleted_at = None
            doc.deleted_by = None
            
            # Optionally restore vector_metadata from deletion log
            deletion_log = (
                sess.query(DocumentDeletionLog)
                .filter(DocumentDeletionLog.document_id == document_id)
                .order_by(DocumentDeletionLog.deleted_at.desc())
                .first()
            )
            
            if deletion_log and deletion_log.vector_metadata_snapshot:
                doc.vector_metadata = deletion_log.vector_metadata_snapshot
            
            return True

    def list_deleted_documents(self, user_id: int) -> List[Dict[str, Any]]:
        """
        List all soft-deleted documents for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of deleted document records
        """
        with self._session_scope() as sess:
            docs = (
                sess.query(Document)
                .filter(
                    Document.user_id == user_id,
                    Document.is_deleted == True  # noqa: E712
                )
                .order_by(Document.deleted_at.desc())
                .all()
            )
            
            return [
                {
                    "id": doc.id,
                    "name": doc.name,
                    "file_type": doc.file_type,
                    "file_size_bytes": doc.file_size_bytes,
                    "deleted_at": doc.deleted_at.isoformat() if doc.deleted_at else None,
                    "deleted_by": doc.deleted_by,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                }
                for doc in docs
            ]

    def permanently_delete_old(self, days: int = 90) -> int:
        """
        Permanently delete documents that have been soft-deleted for a long time.
        
        Args:
            days: Number of days after which to permanently delete
            
        Returns:
            Number of documents permanently deleted
        """
        with self._session_scope() as sess:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted_count = (
                sess.query(Document)
                .filter(
                    Document.is_deleted == True,  # noqa: E712
                    Document.deleted_at < cutoff_date
                )
                .delete(synchronize_session=False)
            )
            
            return deleted_count

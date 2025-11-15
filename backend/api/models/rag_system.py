from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import and_, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from api.db.vector_store import ConversationContext, DocumentEmbedding
from api.utils.config import Config
from api.models.ollama_service import OllamaService

logger = logging.getLogger(__name__)

TARGET_VECTOR_DIM = 384


class RAGSystem:
    """Retrieval-augmented generation backed by local Ollama service."""

    def __init__(self, config: Config, ollama_service: Optional[OllamaService] = None):
        self.config = config
        engine = create_engine(config.database_url, future=True)
        SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        self.engine = engine
        self.session: Session = SessionFactory()

        self.ollama_service: Optional[OllamaService] = ollama_service

        # Optional table names from config.queries (rag section) or defaults
        rag_cfg = (config.queries.get("rag") if isinstance(config.queries, dict) else None) or {}
        self.embed_table: str = rag_cfg.get("embed_table", "data_feeds_vectors.embeddings")
        self.context_table: str = rag_cfg.get("context_table", "conversation_contexts")
        self._cache_ttl = int(os.getenv("RAG_CACHE_TTL", "120"))
        self._query_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
        self._session_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Create useful indexes for faster retrieval and metadata lookups."""
        # Sanitize table reference so generated index names are valid identifiers
        index_table = re.sub(r"[^0-9a-zA-Z_]", "_", self.embed_table)
        statements = [
            f"CREATE INDEX IF NOT EXISTS idx_{index_table}_user_type ON {self.embed_table} (user_id, document_type)",
            f"CREATE INDEX IF NOT EXISTS idx_{index_table}_session_id ON {self.embed_table} ((document_metadata->>'session_id'))",
            f"CREATE INDEX IF NOT EXISTS idx_{index_table}_filename ON {self.embed_table} ((document_metadata->>'filename'))",
            f"CREATE INDEX IF NOT EXISTS idx_{index_table}_embedding ON {self.embed_table} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)",
        ]
        try:
            with self.engine.begin() as conn:
                for stmt in statements:
                    conn.execute(text(stmt))
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Unable to ensure RAG indexes: %s", exc)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def store_document_embedding(
        self,
        user_id: int,
        content: str,
        document_type: str,
        document_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """Generate and persist an embedding for a document."""
        embedding = self._embed_text(content)
        if embedding is None:
            logger.warning("Skipping document embedding; local LLM unavailable.")
            return None

        existing = self._find_existing_embedding(user_id, document_type, metadata)
        timestamp = datetime.utcnow()
        try:
            if existing:
                delta_norm = self._compute_delta_norm(existing.embedding, embedding)
                merged_meta = self._merge_metadata(existing.document_metadata, metadata)
                merged_meta["updated_at"] = timestamp.isoformat()
                if delta_norm is not None:
                    merged_meta["delta_norm"] = delta_norm
                existing.content = content
                existing.embedding = embedding
                existing.document_metadata = merged_meta
                existing.last_used = timestamp
                self.session.commit()
                self._invalidate_cache(user_id)
                logger.info("Updated existing embedding for document type %s", document_type)
                return existing.id

            enriched_meta = dict(metadata or {})
            enriched_meta.setdefault("uploaded_at", timestamp.isoformat())
            record = DocumentEmbedding(
                user_id=user_id,
                document_type=document_type,
                document_id=document_id,
                content=content,
                embedding=embedding,
                document_metadata=enriched_meta,
            )
            self.session.add(record)
            self.session.commit()
            self._invalidate_cache(user_id)
            logger.info("Stored embedding for document type %s", document_type)
            return record.id
        except Exception as exc:  # noqa: BLE001
            self.session.rollback()
            logger.error("Error storing document embedding: %s", exc)
            return None

    def _find_existing_embedding(
        self,
        user_id: int,
        document_type: str,
        metadata: Optional[Dict[str, Any]],
    ) -> Optional[DocumentEmbedding]:
        if not metadata:
            return None
        filename = metadata.get("filename")
        session_id = metadata.get("session_id")
        if not filename:
            return None

        query = (
            self.session.query(DocumentEmbedding)
            .filter(
                DocumentEmbedding.user_id == user_id,
                DocumentEmbedding.document_type == document_type,
                DocumentEmbedding.document_metadata["filename"].astext == filename,
            )
            .order_by(DocumentEmbedding.id.desc())
        )
        if session_id:
            query = query.filter(
                DocumentEmbedding.document_metadata["session_id"].astext == session_id
            )
        return query.first()

    def _compute_delta_norm(
        self, previous: Optional[List[float]], current: List[float]
    ) -> Optional[float]:
        if previous is None:
            return None
        try:
            prev_vec = np.array(previous, dtype=float)
            curr_vec = np.array(current, dtype=float)
            return float(np.linalg.norm(curr_vec - prev_vec))
        except Exception:
            return None

    def _merge_metadata(
        self, existing: Optional[Dict[str, Any]], new_meta: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        merged = dict(existing or {})
        for key, value in (new_meta or {}).items():
            merged[key] = value
        return merged

    def _invalidate_cache(self, user_id: int) -> None:
        prune_keys = [key for key in self._query_cache if key.startswith(f"{user_id}:")]
        for key in prune_keys:
            self._query_cache.pop(key, None)
        prune_sessions = [key for key in self._session_cache if key.startswith(f"{user_id}:")]
        for key in prune_sessions:
            self._session_cache.pop(key, None)

    def _metadata_filter_clause(self, filters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        clauses: List[str] = []
        params: Dict[str, Any] = {}
        if not filters:
            return "", params
        for idx, (key, value) in enumerate(filters.items()):
            if value is None:
                continue
            if not re.match(r"^[a-zA-Z0-9_]+$", key):
                continue
            param_name = f"meta_{idx}"
            clauses.append(f"AND (document_metadata->>'{key}') = :{param_name}")
            params[param_name] = str(value)
        return " ".join(clauses), params

    def _cache_key(
        self,
        user_id: int,
        query: str,
        document_types: Optional[List[str]],
        metadata_filters: Optional[Dict[str, Any]],
    ) -> str:
        types_part = ",".join(sorted(document_types or []))
        meta_part = json.dumps(metadata_filters or {}, sort_keys=True)
        query_hash = hashlib.sha1(query.encode("utf-8")).hexdigest()
        return f"{user_id}:{types_part}:{meta_part}:{query_hash}"

    def _session_cache_key(self, user_id: int, session_id: Optional[str]) -> str:
        return f"{user_id}:{session_id or 'global'}"

    def prime_session_cache(
        self,
        user_id: int,
        session_id: Optional[str],
        document_type: str,
        limit: int = 5,
    ) -> None:
        if not session_id:
            return
        try:
            sql = text(
                f"""
                SELECT id, document_type, document_id, content, document_metadata,
                       0.0 AS similarity_score
                FROM {self.embed_table}
                WHERE user_id = :user_id
                  AND document_type = :doc_type
                  AND (document_metadata->>'session_id') = :session_id
                ORDER BY created_at DESC
                LIMIT :limit
                """
            )
            rows = self.session.execute(
                sql,
                {
                    "user_id": user_id,
                    "doc_type": document_type,
                    "session_id": session_id,
                    "limit": limit,
                },
            ).mappings().all()
            docs = [
                {
                    "id": r["id"],
                    "document_type": r.get("document_type"),
                    "document_id": r.get("document_id"),
                    "content": r.get("content"),
                    "document_metadata": r.get("document_metadata") or {},
                    "similarity_score": r.get("similarity_score"),
                }
                for r in rows
            ]
            self._session_cache[self._session_cache_key(user_id, session_id)] = (time.time(), docs)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Unable to prime session cache: %s", exc)

    def retrieve_similar_documents(
        self,
        query: str,
        user_id: int,
        document_types: Optional[List[str]] = None,
        limit: int = 5,
        session_id: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve similar documents using vector similarity search (pgvector)."""
        metadata_filters = dict(metadata_filters or {})
        if session_id and "session_id" not in metadata_filters:
            metadata_filters["session_id"] = session_id

        cache_key = self._cache_key(user_id, query, document_types, metadata_filters)
        now = time.time()
        cached = self._query_cache.get(cache_key)
        if cached and now - cached[0] < self._cache_ttl:
            return cached[1]

        embedding = self._embed_text(query)
        if embedding is None:
            fallback = self._session_cache.get(self._session_cache_key(user_id, session_id)) if session_id else None
            if fallback and now - fallback[0] < self._cache_ttl:
                return fallback[1]
            return []

        try:
            type_filter = ""
            params: Dict[str, Any] = {
                "query_embedding": embedding,
                "user_id": user_id,
                "limit": limit,
            }
            metadata_clause, metadata_params = self._metadata_filter_clause(metadata_filters)
            params.update(metadata_params)
            if document_types:
                type_filter = "AND document_type = ANY(:doc_types)"
                params["doc_types"] = document_types

            tmpl = (self.config.queries.get("rag") or {}).get("vector_search") or ""

            if tmpl:
                base_sql = tmpl.replace("{embed_table}", self.embed_table)
                sql_text = base_sql.replace("{type_filter}", f" {type_filter} " if type_filter else "")
                sql_text = sql_text.replace("{metadata_filter}", metadata_clause)
            else:
                sql_text = f"""
                    SELECT id, document_type, document_id, content, document_metadata,
                        1 - (embedding <=> :query_embedding) AS similarity_score
                    FROM {self.embed_table}
                    WHERE user_id = :user_id {type_filter} {metadata_clause}
                    ORDER BY embedding <=> :query_embedding
                    LIMIT :limit
                """

            rows = self.session.execute(text(sql_text), params).mappings().all()

            documents: List[Dict[str, Any]] = []

            for r in rows:
                documents.append(
                    {
                        "id": r["id"],
                        "document_type": r.get("document_type"),
                        "document_id": r.get("document_id"),
                        "content": r.get("content"),
                        "document_metadata": r.get("document_metadata") or {},
                        "similarity_score": float(r["similarity_score"]),
                    }
                )

            if documents or metadata_filters:
                self._query_cache[cache_key] = (now, documents)
            if session_id:
                self._session_cache[self._session_cache_key(user_id, session_id)] = (now, documents)
            if not documents and session_id:
                cached_docs = self._session_cache.get(self._session_cache_key(user_id, session_id))
                if cached_docs and now - cached_docs[0] < self._cache_ttl:
                    return cached_docs[1]
            return documents
        except Exception as exc:  # noqa: BLE001
            logger.error("Error retrieving similar documents: %s", exc)
            return []

    def analyze_conversation_context(
        self,
        conversation_text: str,
        user_id: int,
        conversation_id: str,
        conversation_type: str = "call",
    ) -> Dict[str, Any]:
        """Analyze and store conversation context using local LLM."""
        if not self._api_available:
            return {"analysis_complete": False, "error": "local LLM unavailable"}

        analysis = self._analyze_with_llm(conversation_text)
        if not analysis:
            return {"analysis_complete": False, "error": "analysis failed"}

        # Try to embed text for retrieval
        embedding = self._embed_text(conversation_text)

        try:
            context_record = ConversationContext(
                user_id=user_id,
                conversation_id=conversation_id,
                conversation_type=conversation_type,
                context_data=analysis,
                embedding=embedding,
                entities_extracted=analysis.get("entities", []),
                sentiment_score=float(analysis.get("sentiment_score", 0.0)),
                urgency_score=float(analysis.get("urgency_score", 0.0)),
                confidence_score=float(analysis.get("intent_confidence", 0.0)),
            )
            self.session.add(context_record)
            self.session.commit()

            return {
                "context_id": context_record.id,
                "primary_intent": analysis.get("primary_intent"),
                "intent_confidence": float(analysis.get("intent_confidence", 0.0)),
                "sentiment_score": float(analysis.get("sentiment_score", 0.0)),
                "urgency_score": float(analysis.get("urgency_score", 0.0)),
                "entities": analysis.get("entities", []),
                "analysis_complete": True,
            }
        except Exception as exc:  # noqa: BLE001
            self.session.rollback()
            logger.error("Error analyzing conversation context: %s", exc)
            return {"analysis_complete": False, "error": str(exc)}

    def generate_contextual_response(
        self,
        query: str,
        user_id: int,
        conversation_id: Optional[str] = None,
    ) -> str:
        """Produce a conversational response using stored context and local LLM."""
        relevant_docs = self.retrieve_similar_documents(
            query,
            user_id,
            document_types=["instruction", "call_transcript", "contact_info"],
            limit=3,
        )

        conversation_context: Optional[ConversationContext] = None
        if conversation_id:
            conversation_context = (
                self.session.query(ConversationContext)
                .filter_by(conversation_id=conversation_id, user_id=user_id)
                .order_by(ConversationContext.last_updated.desc())
                .first()
            )

        context_parts: List[str] = []
        for doc in relevant_docs:
            snippet = doc["content"][:200].replace("\n", " ")
            context_parts.append(f"Reference snippet: {snippet}")

        if conversation_context:
            ctx = conversation_context.context_data or {}
            context_parts.append(f"Tracked intent: {ctx.get('primary_intent', 'unknown')}")
            context_parts.append(f"Sentiment: {ctx.get('sentiment_label', 'neutral')}")
            if ctx.get("urgency_terms"):
                joined = ", ".join(ctx["urgency_terms"])
                context_parts.append(f"Urgency terms: {joined}")

        context_text = "\n".join(context_parts) or "No additional context available."

        if self._api_available:
            try:
                assert self.ollama_service is not None
                resp = self.ollama_service.generate_response(query=query, context=context_text)
                if resp:
                    return resp.strip()
            except Exception as exc:  # noqa: BLE001
                logger.error("Local generate_response failed: %s", exc)

        return (
            "I'm having trouble generating a response right now. "
            "Please try again once the local AI service is available."
        )

    def update_document_usage(self, document_id: int) -> None:
        """Update usage statistics for an embedding record."""
        try:
            record = self.session.query(DocumentEmbedding).filter_by(id=document_id).first()
            if record:
                record.usage_count = (record.usage_count or 0) + 1
                record.last_used = datetime.utcnow()
                self.session.commit()
        except Exception as exc:  # noqa: BLE001
            self.session.rollback()
            logger.error("Error updating document usage: %s", exc)

    def cleanup(self) -> None:
        """Release database resources."""
        try:
            if hasattr(self, "session") and self.session:
                self.session.close()
        except Exception as exc:  # noqa: BLE001
            logger.error("Error closing RAG session: %s", exc)

        try:
            if hasattr(self, "engine") and self.engine:
                self.engine.dispose()
        except Exception as exc:  # noqa: BLE001
            logger.error("Error disposing RAG engine: %s", exc)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    @property
    def _api_available(self) -> bool:
        return bool(self.ollama_service) and bool(getattr(self.ollama_service, "is_available", lambda: False)())

    def _embed_text(self, text_value: str) -> Optional[List[float]]:
        """Generate an embedding for text using the local Ollama service.

        Returns a 384-dim vector (or down-projects to TARGET_VECTOR_DIM).
        Returns None if the local LLM is unavailable.
        """
        if not text_value or not text_value.strip():
            return self._zero_vector()
        if not self._api_available:
            return None
        try:
            assert self.ollama_service is not None
            embedding = self.ollama_service.generate_embedding(text_value)
            if not embedding:
                return None
            return self._down_project_embedding(embedding)
        except Exception as exc:  # noqa: BLE001
            logger.error("Embedding generation failed: %s", exc)
            return None

    def _zero_vector(self) -> List[float]:
        return [0.0] * TARGET_VECTOR_DIM

    def _down_project_embedding(self, embedding: List[float]) -> List[float]:
        if len(embedding) == TARGET_VECTOR_DIM:
            return embedding
        arr = np.array(embedding, dtype=float)
        if arr.size < TARGET_VECTOR_DIM:
            padded = np.zeros(TARGET_VECTOR_DIM, dtype=float)
            padded[: arr.size] = arr
            return padded.tolist()
        if arr.size % TARGET_VECTOR_DIM == 0:
            factor = arr.size // TARGET_VECTOR_DIM
            reduced = arr.reshape(TARGET_VECTOR_DIM, factor).mean(axis=1)
            return reduced.tolist()
        return arr[:TARGET_VECTOR_DIM].tolist()

    def _safe_json(self, value: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(value)
        except Exception:
            match = re.search(r"\{[\s\S]*\}", value)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    return None
        return None

    def _analyze_with_llm(self, conversation_text: str) -> Optional[Dict[str, Any]]:
        if not self._api_available:
            return None
        instruction = (
            "Extract structured metadata from the conversation. Return pure JSON only with keys: "
            "primary_intent (string), intent_confidence (0-1), sentiment_label (positive|neutral|negative), "
            "sentiment_score (-1..1), urgency_score (0-1), urgency_terms (string[]), entities (objects with type,text)."
        )
        try:
            assert self.ollama_service is not None
            raw = self.ollama_service.generate_response(query=instruction, context=conversation_text)
            if not raw:
                return None
            parsed = self._safe_json(raw)
            return parsed
        except Exception:
            return None

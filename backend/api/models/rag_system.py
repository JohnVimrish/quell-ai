from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import create_engine, text
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
        self.embed_table: str = rag_cfg.get("embed_table", "document_embeddings")
        self.context_table: str = rag_cfg.get("context_table", "conversation_contexts")

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

        try:
            record = DocumentEmbedding(
                user_id=user_id,
                document_type=document_type,
                document_id=document_id,
                content=content,
                embedding=embedding,
                document_metadata=metadata or {},
            )
            self.session.add(record)
            self.session.commit()
            logger.info("Stored embedding for document type %s", document_type)
            return record.id
        except Exception as exc:  # noqa: BLE001
            self.session.rollback()
            logger.error("Error storing document embedding: %s", exc)
            return None

    def retrieve_similar_documents(
        self,
        query: str,
        user_id: int,
        document_types: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve similar documents using vector similarity search (pgvector)."""
        embedding = self._embed_text(query)
        if embedding is None:
            return []

        try:
            type_filter = ""
            params: Dict[str, Any] = {
                "query_embedding": embedding,
                "user_id": user_id,
                "limit": limit,
            }
            if document_types:
                type_filter = "AND document_type = ANY(:doc_types)"
                params["doc_types"] = document_types

            tmpl = (self.config.queries.get("rag") or {}).get("vector_search") or ""

            if tmpl:
                base_sql = tmpl.replace("{embed_table}", self.embed_table)
                sql_text = base_sql.replace("{type_filter}", f" {type_filter} " if type_filter else "")
            else:
                sql_text = f"""
                    SELECT id, document_type, document_id, content, document_metadata,
                        1 - (embedding <=> :query_embedding) AS similarity_score
                    FROM {self.embed_table}
                    WHERE user_id = :user_id {type_filter}
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
                        "document_metadata": r.get("document_metadata"),
                        "similarity_score": float(r["similarity_score"]),
                    }
                )
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



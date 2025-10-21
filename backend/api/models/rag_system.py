from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from api.db.vector_store import ConversationContext, DocumentEmbedding
from api.utils.config import Config

logger = logging.getLogger(__name__)

DEFAULT_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_EMBED_DIM = 1536
TARGET_VECTOR_DIM = 384
OPENAI_TIMEOUT = 30


class RAGSystem:
    """Retrieval-augmented generation backed by OpenAI endpoints."""

    def __init__(self, config: Config):
        self.config = config
        engine = create_engine(config.database_url, future=True)
        SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        self.engine = engine
        self.session: Session = SessionFactory()

        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
        self.chat_model = (
            os.getenv("OPENAI_RAG_MODEL")
            or os.getenv("OPENAI_CHAT_MODEL")
            or os.getenv("LABS_OPENAI_MODEL")
            or DEFAULT_CHAT_MODEL
        )
        self.embed_model = (
            os.getenv("OPENAI_EMBED_MODEL")
            or os.getenv("LABS_OPENAI_EMBED_MODEL")
            or DEFAULT_EMBED_MODEL
        )
        self.embed_dimension = self._resolve_embed_dim()
        self._warned_missing_key = False

        self._urgency_vocab = [
            "urgent",
            "asap",
            "immediately",
            "emergency",
            "critical",
            "help",
            "right away",
        ]
        self._positive_words = ["great", "excellent", "awesome", "thank", "appreciate", "happy"]
        self._negative_words = ["angry", "frustrated", "cancel", "issue", "problem", "upset"]

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
            logger.warning("Skipping document embedding; OpenAI API unavailable.")
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
        """Retrieve similar documents using vector similarity search."""
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

            sql_query = text(
                f"""
                SELECT id, document_type, document_id, content, metadata,
                       1 - (embedding <=> :query_embedding) AS similarity_score
                FROM document_embeddings
                WHERE user_id = :user_id {type_filter}
                ORDER BY embedding <=> :query_embedding
                LIMIT :limit
                """
            )

            rows = self.session.execute(sql_query, params)
            documents: List[Dict[str, Any]] = []
            for row in rows:
                documents.append(
                    {
                        "id": row.id,
                        "document_type": row.document_type,
                        "document_id": row.document_id,
                        "content": row.content,
                        "document_metadata": row.metadata,
                        "similarity_score": float(row.similarity_score),
                    }
                )
            return documents
        except Exception as exc:  # noqa: BLE001
            logger.error("Error retrieving similar documents: %s", exc)
            return []

    def analyze_conversation_context(
        self,
        conversation_text: str,
        conversation_id: str,
        user_id: int,
        conversation_type: str,
    ) -> Dict[str, Any]:
        """Analyze a conversation and persist aggregated context."""
        embedding = self._embed_text(conversation_text) or self._zero_vector()
        analysis = self._analyze_with_openai(conversation_text)

        context_data = {
            "primary_intent": analysis["primary_intent"],
            "intent_confidence": float(analysis["intent_confidence"]),
            "sentiment_label": analysis["sentiment_label"],
            "entities": analysis["entities"],
            "urgency_keywords_found": analysis["urgency_terms"],
            "text_length": len(conversation_text),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

        try:
            context_record = ConversationContext(
                user_id=user_id,
                conversation_id=conversation_id,
                conversation_type=conversation_type,
                context_data=context_data,
                embedding=embedding,
                entities_extracted=analysis["entities"],
                sentiment_score=float(analysis["sentiment_score"]),
                urgency_score=float(analysis["urgency_score"]),
                confidence_score=float(analysis["intent_confidence"]),
            )
            self.session.add(context_record)
            self.session.commit()

            return {
                "context_id": context_record.id,
                "primary_intent": analysis["primary_intent"],
                "intent_confidence": float(analysis["intent_confidence"]),
                "sentiment_score": float(analysis["sentiment_score"]),
                "urgency_score": float(analysis["urgency_score"]),
                "entities": analysis["entities"],
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
        """Produce a conversational response using stored context and OpenAI."""
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
            if ctx.get("urgency_keywords_found"):
                joined = ", ".join(ctx["urgency_keywords_found"])
                context_parts.append(f"Urgency terms: {joined}")

        context_text = "\n".join(context_parts) or "No additional context available."

        response = self._chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant helping with customer communications. "
                        "Use the provided context snippets when helpful. "
                        "If the context lacks relevant facts, be transparent."
                    ),
                },
                {"role": "user", "content": f"Context:\n{context_text}\n\nUser query: {query}"},
            ],
            temperature=0.6,
            max_tokens=400,
        )

        if response:
            return response.strip()
        return (
            "I'm having trouble generating a response right now. "
            "Please try again once the AI services are available."
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
        return bool(self.api_key)

    def _resolve_embed_dim(self) -> int:
        explicit = os.getenv("OPENAI_EMBED_DIM")
        if explicit:
            try:
                return int(explicit)
            except ValueError:
                logger.warning("Invalid OPENAI_EMBED_DIM value '%s'; using defaults.", explicit)

        model = self.embed_model.lower()
        if model in {"text-embedding-3-large"}:
            return 3072
        return DEFAULT_EMBED_DIM

    def _zero_vector(self) -> List[float]:
        return [0.0] * TARGET_VECTOR_DIM

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _log_missing_key(self) -> None:
        if not self._warned_missing_key:
            logger.warning("OPENAI_API_KEY is not configured; falling back to heuristics.")
            self._warned_missing_key = True

    def _embed_text(self, text_value: str) -> Optional[List[float]]:
        if not text_value.strip():
            return self._zero_vector()

        if not self._api_available:
            self._log_missing_key()
            return None

        try:
            payload = {"model": self.embed_model, "input": text_value}
            response = requests.post(
                f"{self.api_base}/embeddings",
                headers=self._headers(),
                json=payload,
                timeout=OPENAI_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            embedding = data["data"][0]["embedding"]
            return self._down_project_embedding(embedding)
        except Exception as exc:  # noqa: BLE001
            logger.error("Embedding request failed: %s", exc)
            return None

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

    def _chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 500,
    ) -> Optional[str]:
        if not self._api_available:
            self._log_missing_key()
            return None

        try:
            payload = {
                "model": self.chat_model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=OPENAI_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            logger.error("Chat completion failed: %s", exc)
            return None

    def _analyze_with_openai(self, conversation_text: str) -> Dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You extract structured metadata from conversations. "
                    "Return pure JSON with the keys: primary_intent (string), "
                    "intent_confidence (float 0-1), sentiment_label (positive|neutral|negative), "
                    "sentiment_score (float -1..1), urgency_score (float 0-1), "
                    "urgency_terms (array of strings), and entities (array of objects "
                    "with 'type' and 'text')."
                ),
            },
            {"role": "user", "content": conversation_text},
        ]

        raw = self._chat_completion(messages, temperature=0.2, max_tokens=400)
        if not raw:
            return self._simple_analysis_fallback(conversation_text)

        parsed = self._safe_json(raw)
        if not parsed:
            return self._simple_analysis_fallback(conversation_text)

        return self._normalize_analysis(parsed, conversation_text)

    def _safe_json(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"{.*}", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    return None
        return None

    def _normalize_analysis(self, data: Dict[str, Any], text_value: str) -> Dict[str, Any]:
        fallback = self._simple_analysis_fallback(text_value)

        def _float(key: str, default: float) -> float:
            value = data.get(key, default)
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        primary_intent = str(data.get("primary_intent") or fallback["primary_intent"]).strip() or fallback["primary_intent"]
        intent_confidence = max(0.0, min(1.0, _float("intent_confidence", fallback["intent_confidence"])))
        sentiment_label = str(data.get("sentiment_label") or fallback["sentiment_label"]).lower()
        if sentiment_label not in {"positive", "neutral", "negative"}:
            sentiment_label = fallback["sentiment_label"]

        sentiment_score = float(np.clip(_float("sentiment_score", fallback["sentiment_score"]), -1.0, 1.0))
        urgency_score = max(0.0, min(1.0, _float("urgency_score", fallback["urgency_score"])))

        urgency_terms = data.get("urgency_terms") or fallback["urgency_terms"]
        if isinstance(urgency_terms, list):
            urgency_terms = [str(term).strip() for term in urgency_terms if str(term).strip()]
        else:
            urgency_terms = fallback["urgency_terms"]

        entities_raw = data.get("entities") or fallback["entities"]
        entities: List[Dict[str, Any]] = []
        if isinstance(entities_raw, list):
            for item in entities_raw:
                if isinstance(item, dict) and item.get("text"):
                    entities.append(
                        {
                            "type": str(item.get("type", "unknown")),
                            "text": str(item.get("text")),
                        }
                    )
                elif isinstance(item, str) and item.strip():
                    entities.append({"type": "unknown", "text": item.strip()})
        else:
            entities = fallback["entities"]

        return {
            "primary_intent": primary_intent,
            "intent_confidence": intent_confidence,
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "urgency_score": urgency_score,
            "urgency_terms": urgency_terms,
            "entities": entities,
        }

    def _simple_analysis_fallback(self, text_value: str) -> Dict[str, Any]:
        lower = text_value.lower()
        pos_hits = sum(lower.count(word) for word in self._positive_words)
        neg_hits = sum(lower.count(word) for word in self._negative_words)
        total_hits = pos_hits + neg_hits

        sentiment_score = 0.0
        if total_hits:
            sentiment_score = (pos_hits - neg_hits) / max(total_hits, 1)

        sentiment_label = "neutral"
        if sentiment_score > 0.2:
            sentiment_label = "positive"
        elif sentiment_score < -0.2:
            sentiment_label = "negative"

        urgency_terms = [term for term in self._urgency_vocab if term in lower]
        urgency_score = min(len(urgency_terms) / max(len(self._urgency_vocab), 1), 1.0)

        primary_intent = "general_inquiry"
        if "schedule" in lower or "meeting" in lower:
            primary_intent = "appointment_scheduling"
        elif "complain" in lower or "frustrated" in lower or sentiment_label == "negative":
            primary_intent = "complaint"
        elif urgency_score > 0.4:
            primary_intent = "urgent_request"

        entities: List[Dict[str, Any]] = []
        email_matches = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text_value)
        for email in email_matches:
            entities.append({"type": "email", "text": email})

        phone_matches = re.findall(r"\+?\d[\d\s().-]{7,}", text_value)
        for phone in phone_matches:
            entities.append({"type": "phone_number", "text": phone.strip()})

        return {
            "primary_intent": primary_intent,
            "intent_confidence": 0.55,
            "sentiment_label": sentiment_label,
            "sentiment_score": float(np.clip(sentiment_score, -1.0, 1.0)),
            "urgency_score": urgency_score,
            "urgency_terms": urgency_terms,
            "entities": entities,
        }


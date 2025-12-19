"""
Minimal Ollama wrapper aligned with the smoke-test helper.
Keeps the public interface expected by the rest of the backend
while relying entirely on the official `ollama` Python package.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Callable, List, Optional

import httpx
import ollama

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = os.getenv("DEFAULT_OLLAMA_MODEL_NAME", "mistral:latest")
DEFAULT_OLLAMA_URL = os.getenv("DEFAULT_OLLAMA_URL", "http://localhost:11434")
CHUNK_LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "ollama_chunks.log"
CHUNK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


class OllamaTimeoutError(RuntimeError):
    """Raised when a request to the Ollama API exceeds the configured timeout."""


class OllamaService:
    def __init__(self, embedding_dim: Optional[int] = None) -> None:
        self.model_name = os.getenv("OLLAMA_MODEL_NAME", DEFAULT_MODEL_NAME)
        self.base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL)
        self.embedding_dim = embedding_dim or int(os.getenv("OLLAMA_EMBEDDING_DIM", "384"))
        self._timeout = None
        self.client = self._create_client()
        self.model_loaded = self._ensure_model_available()

    # ------------------------------------------------------------------
    # Client helpers
    # ------------------------------------------------------------------
    def _create_client(self):
        client_cls = getattr(ollama, "Client", None)
        if client_cls:
            try:
                params = {"host": self.base_url}
                if self._timeout is not None:
                    params["timeout"] = self._timeout
                return client_cls(**params)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Unable to initialize Ollama client (%s); falling back to module API", exc)
        os.environ.setdefault("OLLAMA_HOST", self.base_url)
        return None

    def _ensure_model_available(self) -> bool:
        try:
            info = self.client.list() if self.client else ollama.list()
            for entry in info.get("models", []):
                if self.model_name in (entry.get("name"), entry.get("model")):
                    return True
            logger.warning(
                "Model '%s' not installed on %s. Run `ollama pull %s`.",
                self.model_name,
                self.base_url,
                self.model_name,
            )
            return False
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unable to reach Ollama host %s: %s", self.base_url, exc)
            return False

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    def _call_embeddings(self, text: str) -> Optional[dict]:
        if not text.strip():
            return None
        params = {"model": self.model_name, "prompt": text}
        try:
            if self.client:
                return self.client.embeddings(**params)
            return ollama.embeddings(**params)
        except httpx.TimeoutException as exc:
            logger.error("Embedding request timed out: %s", exc)
            raise OllamaTimeoutError("Embedding request timed out.") from exc
        except Exception as exc:  # noqa: BLE001
            logger.error("Embedding request failed: %s", exc, exc_info=True)
            return None

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        payload = self._call_embeddings(text)
        embedding = (payload or {}).get("embedding")
        if not embedding:
            return self._zero_vector()
        return self._adjust_dimension(embedding)

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        return [self.generate_embedding(text) or self._zero_vector() for text in texts]

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def _chat(self, prompt: str, stream: bool):
        params = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
        }
        try:
            if self.client:
                return self.client.chat(**params)
            return ollama.chat(**params)
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError("Chat request timed out.") from exc

    def generate_response(
        self,
        query: str,
        context: str,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        prompt = self._build_prompt(query, context)
        start_time = time.time()
        self._record_chunk_event(
            f"request_start model={self.model_name} query_snippet={query[:80]!r}"
        )
        try:
            if on_chunk:
                stream = self._chat(prompt, stream=True)
                parts: List[str] = []
                for chunk in stream:
                    delta = (chunk or {}).get("message", {}).get("content", "")
                    if not delta:
                        continue
                    parts.append(delta)
                    self._record_chunk_event(
                        f"chunk len={len(delta)} elapsed={time.time()-start_time:.2f}s snippet={delta[:80]!r}"
                    )
                    on_chunk(delta)
                response_text = "".join(parts)
            else:
                payload = self._chat(prompt, stream=False)
                response_text = (
                    payload.get("message", {}).get("content")
                    or payload.get("response")
                    or payload.get("generated_text")
                    or ""
                )
                self._record_chunk_event(
                    f"non_stream_response len={len(response_text)} elapsed={time.time()-start_time:.2f}s"
                )
            self._record_chunk_event(
                f"request_complete total_elapsed={time.time()-start_time:.2f}s"
            )
            return response_text.strip() or "I couldn't generate a meaningful response."
        except OllamaTimeoutError as exc:
            logger.error("Chat request timed out: %s", exc)
            self._record_chunk_event(
                f"request_timeout elapsed={time.time()-start_time:.2f}s error={exc}"
            )
            return "The language model is taking too long to respond. Please retry in a moment."
        except Exception as exc:  # noqa: BLE001
            logger.error("Chat request failed: %s", exc, exc_info=True)
            self._record_chunk_event(
                f"request_error elapsed={time.time()-start_time:.2f}s error={exc}"
            )
            return (
                "I encountered an error while generating a response. "
                "Please try again or verify the Ollama service."
            )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _build_prompt(self, query: str, context: str) -> str:
        return f"""Context information:
{context}

User question: {query}

Based on the context above, provide a helpful and accurate response."""

    def _adjust_dimension(self, vector: List[float]) -> List[float]:
        if len(vector) == self.embedding_dim:
            return vector
        if len(vector) < self.embedding_dim:
            return vector + [0.0] * (self.embedding_dim - len(vector))
        return vector[:self.embedding_dim]

    def _zero_vector(self) -> List[float]:
        return [0.0] * self.embedding_dim

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        if self.model_loaded:
            return True
        self.model_loaded = self._ensure_model_available()
        return self.model_loaded

    def get_model_info(self) -> dict:
        return {
            "mode": "ollama",
            "model_name": self.model_name,
            "model_path": None,
            "embedding_dim": self.embedding_dim,
            "model_loaded": self.model_loaded,
            "host": self.base_url,
        }

    def compare_embeddings(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        if not embedding1 or not embedding2 or len(embedding1) != len(embedding2):
            return 0.0
        try:
            import numpy as np

            vec1 = np.array(embedding1, dtype=float)
            vec2 = np.array(embedding2, dtype=float)
            dot = float(np.dot(vec1, vec2))
            denom = float(np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return dot / denom if denom else 0.0
        except Exception as exc:  # noqa: BLE001
            logger.error("Error comparing embeddings: %s", exc, exc_info=True)
            return 0.0

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------
    def _record_chunk_event(self, message: str) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        line = f"[{timestamp}] {message}\n"
        try:
            with CHUNK_LOG_PATH.open("a", encoding="utf-8") as handle:
                handle.write(line)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to write chunk log: %s", exc)

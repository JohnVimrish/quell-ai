"""
Embedding provider abstraction that can source vectors from different backends.
Currently supports:
  - sentence-transformers (default)
  - Ollama (legacy path)
"""
from __future__ import annotations

import logging
import os
import threading
from typing import List, Optional

from pathlib import Path
import time

from api.models.ollama_service import OllamaService, OllamaTimeoutError

logger = logging.getLogger(__name__)

try:  # Optional dependency already listed in extras/requirements.txt
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover - import guard
    SentenceTransformer = None  # type: ignore


EMBED_LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "embedding_backend.log"
EMBED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _record_event(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"[{timestamp}] {message}\n"
    try:
        with EMBED_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line)
    except Exception:  # pragma: no cover - best effort
        logger.debug("Unable to write embedding log entry.")


class EmbeddingTimeoutError(RuntimeError):
    """Raised when a backend exceeds its timeout window."""


class BaseEmbeddingBackend:
    label = "unknown"

    def embed(self, text: str) -> Optional[List[float]]:
        raise NotImplementedError


class OllamaEmbeddingBackend(BaseEmbeddingBackend):
    def __init__(self, service: Optional[OllamaService]) -> None:
        self._service = service
        self.label = "ollama"

    def embed(self, text: str) -> Optional[List[float]]:
        if not self._service or not self._service.is_available():
            return None
        start = time.time()
        _record_event(f"backend={self.label} event=start chars={len(text)}")
        try:
            vector = self._service.generate_embedding(text)
            elapsed = time.time() - start
            _record_event(f"backend={self.label} event=success elapsed={elapsed:.2f}s dim={len(vector) if vector else 0}")
            return vector
        except OllamaTimeoutError as exc:  # pragma: no cover - passthrough
            _record_event(f"backend={self.label} event=timeout elapsed={time.time()-start:.2f}s")
            raise EmbeddingTimeoutError("Embedding request timed out.") from exc
        except Exception as exc:  # pragma: no cover - best effort logging
            logger.error("Ollama embedding failed: %s", exc, exc_info=True)
            _record_event(f"backend={self.label} event=error error={exc}")
            return None


class SentenceTransformerBackend(BaseEmbeddingBackend):
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None) -> None:
        self.model_name = model_name or os.getenv(
            "SENTENCE_TRANSFORMER_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )
        self.device = device or os.getenv("SENTENCE_TRANSFORMER_DEVICE")
        self._model: Optional[SentenceTransformer] = None  # type: ignore[assignment]
        self._load_lock = threading.Lock()
        self.label = f"sentence_transformer:{self.model_name}"

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        if SentenceTransformer is None:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Install extras/requirements.txt or set EMBEDDING_BACKEND=ollama."
            )
        with self._load_lock:
            if self._model is None:
                logger.info("Loading sentence-transformer model %s", self.model_name)
                self._model = SentenceTransformer(self.model_name, device=self.device)  # type: ignore[call-arg]

    def embed(self, text: str) -> Optional[List[float]]:
        if not text.strip():
            return [0.0]
        self._ensure_model()
        assert self._model is not None
        start = time.time()
        _record_event(f"backend={self.label} event=start chars={len(text)}")
        try:
            vector = self._model.encode(text, normalize_embeddings=False)
            _record_event(f"backend={self.label} event=success elapsed={time.time()-start:.2f}s dim={len(vector)}")
            return vector.tolist()
        except Exception as exc:  # pragma: no cover - best effort logging
            logger.error("SentenceTransformer embedding failed: %s", exc, exc_info=True)
            _record_event(f"backend={self.label} event=error error={exc}")
            return None


def get_embedding_backend(ollama_service: Optional[OllamaService]) -> BaseEmbeddingBackend:
    """Return the configured embedding backend."""
    preference = (os.getenv("EMBEDDING_BACKEND") or "sentence_transformer").strip().lower()

    def _choose(order: List[str]) -> BaseEmbeddingBackend:
        for option in order:
            if option == "sentence_transformer":
                try:
                    return SentenceTransformerBackend()
                except Exception as exc:
                    logger.warning("SentenceTransformer backend unavailable: %s", exc)
            elif option == "ollama":
                return OllamaEmbeddingBackend(ollama_service)
        # Fallback to Ollama even if preference was sentence transformer but it failed.
        return OllamaEmbeddingBackend(ollama_service)

    if preference in {"ollama"}:
        return _choose(["ollama", "sentence_transformer"])
    return _choose(["sentence_transformer", "ollama"])


__all__ = [
    "EmbeddingTimeoutError",
    "BaseEmbeddingBackend",
    "OllamaEmbeddingBackend",
    "SentenceTransformerBackend",
    "get_embedding_backend",
]

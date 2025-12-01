from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Optional

from api.models.ollama_service import OllamaService

logger = logging.getLogger(__name__)


class _TTLCache:
    def __init__(self, maxsize: int = 128, ttl_seconds: int = 120) -> None:
        self.maxsize = maxsize
        self.ttl = ttl_seconds
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            data = self._store.get(key)
            if not data:
                return None
            timestamp, value = data
            if time.time() - timestamp > self.ttl:
                self._store.pop(key, None)
                return None
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.time(), value)
            self._store.move_to_end(key)
            while len(self._store) > self.maxsize:
                self._store.popitem(last=False)


class EmbeddingQueue:
    """Threaded queue that reuses a small pool of embedding workers."""

    def __init__(
        self,
        ollama_service: OllamaService,
        *,
        max_workers: int = 2,
        cache_size: int = 128,
        cache_ttl_seconds: int = 180,
        default_timeout: int = 60,
    ) -> None:
        self._ollama = ollama_service
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="embedding-worker")
        self._cache = _TTLCache(maxsize=cache_size, ttl_seconds=cache_ttl_seconds)
        self._default_timeout = default_timeout

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def embed(self, text: str, *, timeout: Optional[int] = None) -> Optional[list[float]]:
        text = text or ""
        cache_key = hashlib.sha1(text.encode("utf-8")).hexdigest()
        cached = self._cache.get(cache_key)
        if cached is not None:
            return list(cached)
        if not self._ollama or not self._ollama.is_available():
            return None

        def _task() -> Optional[list[float]]:
            try:
                vector = self._ollama.generate_embedding(text)
                if vector:
                    self._cache.set(cache_key, list(vector))
                return vector
            except Exception as exc:  # noqa: BLE001
                logger.warning("Embedding queue worker failed: %s", exc)
                return None

        future: Future[Optional[list[float]]] = self._executor.submit(_task)
        wait_for = timeout or self._default_timeout
        return future.result(timeout=wait_for)

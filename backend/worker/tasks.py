from __future__ import annotations

import logging
import os
import json
from datetime import datetime
import time
from pathlib import Path
from typing import Optional, List, Any, Dict
import threading

from sqlalchemy.orm import sessionmaker
from flask_socketio import SocketIO

from worker.celery_app import celery_app

from api.app import create_app
from api.db.vector_store import ConversationLabIngest
from api.services.labs_ingest import summarize_ingest_payload, store_embedding_for_upload, serialize_ingest_row
from scripts.ingest_file import ingest_single_file

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore

# Lazy-initialized Flask app + DB session for workers
flask_app = None
rag_system = None
SessionLocal = None

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs" / "ingest"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"{datetime.utcnow():%Y%m%d}.log"

ingest_logger = logging.getLogger("ingest")
if not ingest_logger.handlers:
    handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    ingest_logger.addHandler(handler)
ingest_logger.setLevel(logging.INFO)

SOCKETIO_QUEUE = os.getenv("SOCKETIO_MESSAGE_QUEUE")
if SOCKETIO_QUEUE:
    try:
        socketio_notifier = SocketIO(message_queue=SOCKETIO_QUEUE)
    except Exception as exc:
        ingest_logger.warning("SocketIO message queue unavailable (%s). Disabling ingest events.", exc)
        socketio_notifier = None
else:
    socketio_notifier = None

fallback_model_name = os.getenv("FALLBACK_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
fallback_embedder = None
PRIME_DEBOUNCE_SECONDS = int(os.getenv("PRIME_SESSION_DEBOUNCE", "60"))
_prime_tracker: Dict[str, float] = {}
_prime_lock = threading.Lock()

class IngestJobError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _ensure_worker_app() -> None:
    global flask_app, rag_system, SessionLocal
    if flask_app is None:
        flask_app = create_app()
        rag_system = flask_app.config.get("RAG_SYSTEM")
        if rag_system and getattr(rag_system, "engine", None):
            SessionLocal = sessionmaker(bind=rag_system.engine)


def _emit_ingest_event(row: ConversationLabIngest) -> None:
    if socketio_notifier and row.session_id:
        try:
            payload = serialize_ingest_row(row)
            socketio_notifier.emit("ingest_update", payload, room=f"ingest:{row.session_id}")
        except Exception:
            ingest_logger.exception("Failed to emit ingest event for %s", row.id)


def _log_ingest_event(level: str, payload: Dict[str, Any]) -> None:
    try:
        message = json.dumps(payload, default=str, ensure_ascii=False)
    except Exception:
        message = str(payload)
    log_fn = getattr(ingest_logger, level, ingest_logger.info)
    log_fn(message)


def _set_progress_stage(
    session,
    row: ConversationLabIngest,
    stage: str,
    detail: Optional[str] = None,
) -> None:
    metadata = dict(row.ingest_metadata or {})
    metadata["progress_stage"] = stage
    if detail is not None:
        metadata["progress_detail"] = detail
    row.ingest_metadata = metadata
    session.add(row)
    session.commit()
    _emit_ingest_event(row)
    _log_ingest_event(
        "info",
        {
            "ingest_id": row.id,
            "stage": stage,
            "detail": detail,
        },
    )


def _fallback_embedding(text: str) -> Optional[List[float]]:
    global fallback_embedder
    if not text.strip() or SentenceTransformer is None:
        return None
    if fallback_embedder is None:
        try:
            fallback_embedder = SentenceTransformer(fallback_model_name)
        except Exception as exc:  # pragma: no cover
            ingest_logger.error("Fallback embedding model failed to load: %s", exc)
            return None
    try:
        vector = fallback_embedder.encode(text, normalize_embeddings=False)
        return vector.tolist()
    except Exception as exc:
        ingest_logger.error("Fallback embedding generation failed: %s", exc)
        return None


def _maybe_prime_session_cache(user_id: int, session_id: Optional[str]) -> None:
    if not session_id or rag_system is None:
        return
    key = f"{user_id}:{session_id}"
    now = time.time()
    with _prime_lock:
        last_run = _prime_tracker.get(key)
        if last_run and now - last_run < PRIME_DEBOUNCE_SECONDS:
            return
        _prime_tracker[key] = now
    try:
        rag_system.prime_session_cache(
            user_id=user_id,
            session_id=session_id,
            document_type="conversation_lab_upload",
        )
    except Exception as exc:  # pragma: no cover - best effort
        ingest_logger.warning("Session cache prime failed for %s: %s", key, exc)


def _update_row_status(
    session,
    row: ConversationLabIngest,
    *,
    status: str,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    row.status = status
    row.error_code = error_code
    row.error_message = error_message
    if status == "processing":
        row.started_at = datetime.utcnow()
    row.finished_at = datetime.utcnow() if status in {"ready", "failed"} else row.finished_at
    session.add(row)
    session.commit()
    _emit_ingest_event(row)
    _log_ingest_event(
        "info",
        {
            "ingest_id": row.id,
            "status": status,
            "error_code": error_code,
        },
    )


@celery_app.task(name="ingest.process_conversation_lab_ingest")
def process_conversation_lab_ingest(ingest_id: int) -> None:
    _ensure_worker_app()
    if SessionLocal is None or rag_system is None:
        ingest_logger.error("Worker not configured with database or RAG system")
        return

    session = SessionLocal()
    row: Optional[ConversationLabIngest] = None
    try:
        row = session.get(ConversationLabIngest, ingest_id)
        if row is None:
            ingest_logger.warning("Ingest row %s not found", ingest_id)
            return

        row.attempts = (row.attempts or 0) + 1
        session.add(row)
        session.commit()

        _update_row_status(session, row, status="processing")
        _set_progress_stage(session, row, "processing")

        storage_path = row.storage_path
        if not storage_path or not os.path.exists(storage_path):
            raise IngestJobError("payload_missing", f"Payload for {row.filename} is unavailable.")

        with open(storage_path, "rb") as fh:
            file_bytes = fh.read()

        description = (row.ingest_metadata or {}).get("description") or "Conversation Lab upload"
        try:
            result = ingest_single_file(
                file_path=None,
                file_data=file_bytes,
                filename_override=row.filename,
                save=False,
                user_id=row.user_id,
                description=description,
                classification="internal",
                ask=None,
                user_email=None,
            )
        except ValueError as exc:
            raise IngestJobError("validation_error", str(exc)) from exc
        except Exception as exc:
            raise IngestJobError("ingest_exception", str(exc)) from exc

        if not result:
            raise IngestJobError("pipeline_error", "Ingestion pipeline returned an empty result.")
        if result.get("ok") is False:
            raise IngestJobError("pipeline_error", result.get("error") or "ingestion failed")

        language = result.get("language") or "unknown"
        _set_progress_stage(session, row, "parsed", detail=f"language={language}")
        if result.get("translated_to_english"):
            _set_progress_stage(session, row, "translated", detail="translated_to_english")

        summary = summarize_ingest_payload(result)
        metadata = row.ingest_metadata or {}
        metadata.update(
            {
                "summary": summary,
                "analytics": result.get("analytics") or {},
                "concepts": result.get("concepts") or {},
                "language": result.get("language"),
            }
        )

        extra_meta = dict(metadata)
        extra_meta.update(
            {
                "session_id": row.session_id,
                "filename": row.filename,
                "file_hash": metadata.get("file_hash"),
            }
        )
        processed_content = result.get("processed_content") or ""
        _set_progress_stage(session, row, "embedding", detail="primary")
        embedding_id = store_embedding_for_upload(
            rag_system,
            row.user_id,
            processed_content,
            extra_meta,
        )
        if embedding_id is None:
            fallback_vector = _fallback_embedding(processed_content)
            if fallback_vector is not None:
                ingest_logger.info("ingest_id=%s using fallback embedding model %s", row.id, fallback_model_name)
                _set_progress_stage(session, row, "embedding", detail="fallback")
                extra_meta["embedding_model"] = fallback_model_name
                embedding_id = store_embedding_for_upload(
                    rag_system,
                    row.user_id,
                    processed_content,
                    extra_meta,
                    embedding_override=fallback_vector,
                )

        metadata["rag_document_id"] = embedding_id
        metadata["processed_preview"] = processed_content[:1000]
        metadata["progress_stage"] = "ready"
        metadata["progress_detail"] = None
        row.ingest_metadata = metadata
        row.embedding_id = embedding_id
        row.needs_embedding = embedding_id is None
        row.status = "ready"
        row.finished_at = datetime.utcnow()
        session.add(row)
        session.commit()
        _emit_ingest_event(row)
        _log_ingest_event(
            "info",
            {
                "ingest_id": row.id,
                "status": "ready",
                "embedding_id": embedding_id,
            },
        )
        _maybe_prime_session_cache(row.user_id, row.session_id)
    except IngestJobError as exc:
        session.rollback()
        if row is not None:
            row.status = "failed"
            row.error_code = exc.code
            row.error_message = str(exc)
            row.finished_at = datetime.utcnow()
            session.add(row)
            session.commit()
            _emit_ingest_event(row)
            ingest_logger.error("ingest_id=%s code=%s error=%s", row.id, exc.code, exc)
            _log_ingest_event(
                "error",
                {
                    "ingest_id": row.id,
                    "status": "failed",
                    "error_code": exc.code,
                    "error_message": str(exc),
                },
            )
        else:
            ingest_logger.exception("Failed before ingest row loaded: %s", exc)
    except Exception as exc:
        session.rollback()
        if row is not None:
            row.status = "failed"
            row.error_code = getattr(exc, "code", None) or "ingest_error"
            row.error_message = str(exc)
            row.finished_at = datetime.utcnow()
            session.add(row)
            session.commit()
            _emit_ingest_event(row)
            ingest_logger.exception("ingest_id=%s failed: %s", row.id, exc)
            _log_ingest_event(
                "error",
                {
                    "ingest_id": row.id,
                    "status": "failed",
                    "error_code": getattr(exc, "code", None) or "ingest_error",
                    "error_message": str(exc),
                },
            )
        else:
            ingest_logger.exception("Failed before ingest row loaded: %s", exc)
    finally:
        session.close()


def enqueue_conversation_lab_ingest(ingest_id: int) -> None:
    process_conversation_lab_ingest.delay(ingest_id)

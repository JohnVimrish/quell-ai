from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from api.db.vector_store import ConversationLabIngest
from api.models.rag_system import RAGSystem


def summarize_ingest_payload(payload: Dict[str, Any]) -> str:
    analytics = payload.get("analytics") or {}
    file_type = payload.get("file_type") or ""
    pieces: List[str] = []

    if "row_count" in analytics:
        row_count = analytics.get("row_count")
        col_count = analytics.get("column_count")
        pieces.append(f"{row_count} row{'s' if row_count != 1 else ''}")
        if col_count is not None:
            pieces.append(f"{col_count} column{'s' if col_count != 1 else ''}")
    elif "word_count" in analytics:
        words = analytics.get("word_count")
        lines = analytics.get("line_count")
        pieces.append(f"{words} words")
        if lines is not None:
            pieces.append(f"{lines} lines")
    elif "char_count" in analytics:
        pieces.append(f"{analytics.get('char_count')} characters")

    if not pieces:
        pieces.append("Processed document")

    if file_type:
        pieces.append(file_type.upper())

    language = payload.get("language")
    if language and language not in {"en", "english"}:
        pieces.append(f"language {language}")

    return " · ".join(str(part) for part in pieces if part)


def store_embedding_for_upload(
    rag: Optional[RAGSystem],
    user_id: int,
    processed_text: str,
    metadata: Dict[str, Any],
    *,
    embedding_override: Optional[List[float]] = None,
) -> Optional[int]:
    if not (rag and processed_text):
        return None
    safe_meta = dict(metadata or {})
    safe_meta.update({"source": "conversation_lab"})
    if "file_hash" not in safe_meta:
        safe_meta["file_hash"] = hashlib.sha256(processed_text.encode("utf-8", "ignore")).hexdigest()
    timestamp = datetime.utcnow().isoformat()
    safe_meta.setdefault("uploaded_at", timestamp)
    safe_meta["updated_at"] = timestamp

    try:
        doc_id = rag.store_document_embedding(
            user_id=user_id,
            content=processed_text,
            document_type="conversation_lab_upload",
            metadata=safe_meta,
            embedding_override=embedding_override,
        )
    except Exception:
        return None

    return doc_id


def serialize_ingest_row(row: ConversationLabIngest) -> Dict[str, Any]:
    metadata = row.ingest_metadata or {}
    return {
        "id": row.id,
        "sessionId": row.session_id,
        "filename": row.filename,
        "fileType": row.file_type,
        "fileSizeBytes": row.file_size_bytes,
        "status": row.status,
        "errorCode": row.error_code,
        "errorMessage": row.error_message,
        "queuedAt": row.queued_at.isoformat() if row.queued_at else None,
        "startedAt": row.started_at.isoformat() if row.started_at else None,
        "finishedAt": row.finished_at.isoformat() if row.finished_at else None,
        "summary": metadata.get("summary"),
        "analytics": metadata.get("analytics"),
        "concepts": metadata.get("concepts"),
        "language": metadata.get("language"),
        "processedPreview": metadata.get("processed_preview"),
        "ragDocumentId": row.embedding_id,
        "progressStage": metadata.get("progress_stage"),
        "progressDetail": metadata.get("progress_detail"),
        "fileHash": metadata.get("file_hash"),
        "clientSignature": metadata.get("client_signature"),
    }

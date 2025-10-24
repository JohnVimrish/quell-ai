from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.utils import secure_filename

from api.repositories.documents_repo import DocumentsRepository
from api.utils.file_processors import (
    process_file,
    process_text_input,
    validate_file_size,
)
from api.utils.metadata_extractor import build_vector_metadata, extract_key_concepts
from api.utils.nlp_utils import detect_language, translate_to_english
from api.utils.analytics import analyze_text, analyze_table, analyze_json

logger = logging.getLogger(__name__)

bp = Blueprint("documents", __name__)

ALLOWED_EXTENSIONS = {"txt", "csv", "xlsx"}


def require_auth():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_directory() -> Path:
    upload_dir = Path(os.getenv("DATA_FEEDS_UPLOAD_DIR", "backend/uploads/data_feeds"))
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@bp.get("")
def list_documents():
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    docs = repo.list_documents(user_id)
    return jsonify({"documents": docs})


@bp.post("/upload")
def upload_file():
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    if "file" not in request.files:
        return jsonify({"error": "no file provided"}), 400

    files = request.files.getlist("file")
    valid_exts = set(ALLOWED_EXTENSIONS) | {"json"}

    results: List[dict] = []

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    ollama_service = current_app.config.get("OLLAMA_SERVICE")
    rag_system = current_app.config.get("RAG_SYSTEM")

    description = request.form.get("description", "")
    classification = request.form.get("classification", "internal")

    for file in files:
        if not file or file.filename == "":
            results.append({"error": "no file selected"})
            continue

        if "." not in file.filename or file.filename.rsplit(".", 1)[1].lower() not in valid_exts:
            results.append(
                {
                    "error": f"file type not allowed. Supported types: {', '.join(sorted(valid_exts))}",
                    "name": file.filename,
                }
            )
            continue

        try:
            file_data = file.read()
            file_size = len(file_data)

            is_valid, error_msg = validate_file_size(file_size)
            if not is_valid:
                results.append({"error": error_msg, "name": file.filename})
                continue

            filename = secure_filename(file.filename)
            file_type = filename.rsplit(".", 1)[1].lower()

            parsed = process_file(file_data, filename, file_type)
            if not parsed["success"]:
                error = parsed.get("metadata", {}).get("error", "Failed to process file")
                results.append({"error": error, "name": filename})
                continue

            base_text = parsed.get("processed_content", "")

            lang_code = detect_language(base_text)
            translated_by = None
            processed_text = base_text
            if lang_code and lang_code not in ("en", "unknown"):
                processed_text, translated_by = translate_to_english(base_text, ollama_service)

            analytics = {}
            if parsed.get("rows") is not None and parsed.get("columns") is not None:
                analytics = analyze_table(parsed.get("rows", []), parsed.get("columns", []))
            elif file_type == "json":
                analytics = analyze_json(parsed.get("json_data")) if parsed.get("json_data") is not None else {}
            else:
                analytics = analyze_text(processed_text)

            concepts = extract_key_concepts(processed_text, ollama_service)

            embedding = None
            ollama_model = None
            if ollama_service and ollama_service.is_available():
                embedding = ollama_service.generate_embedding(processed_text)
                model_info = ollama_service.get_model_info()
                ollama_model = f"{model_info.get('model_path', 'unknown')}"

            vector_metadata = build_vector_metadata(concepts, embedding)

            existing_doc = repo.check_existing_document(filename, user_id)
            if existing_doc and embedding and existing_doc.get("embedding") is not None and ollama_service:
                similarity = ollama_service.compare_embeddings(existing_doc["embedding"], embedding)
                logger.info(f"Embedding similarity for '{filename}': {similarity:.4f}")
                if similarity > 0.95:
                    logger.info(
                        f"File '{filename}' unchanged (similarity {similarity:.4f}), returning existing document"
                    )
                    document = repo.get_document(existing_doc["id"], user_id)
                    # Update RAG embedding as well (best-effort)
                    try:
                        if rag_system:
                            rag_system.store_document_embedding(
                                user_id, processed_text, "document", existing_doc["id"], {"name": filename}
                            )
                    except Exception:
                        logger.warning("RAG embedding update failed", exc_info=True)

                    results.append(
                        {
                            **(document or {}),
                            "message": "File content unchanged, existing document returned",
                            "similarity_score": similarity,
                            "reprocessed": False,
                            "analytics": analytics,
                        }
                    )
                    continue

                # Create version snapshot and update
                try:
                    repo.create_version_snapshot(
                        document_id=existing_doc["id"],
                        version=existing_doc.get("version", 1),
                        embedding=existing_doc.get("embedding"),
                        content_snapshot=processed_text[:1000],
                        metadata_snapshot=existing_doc.get("content_metadata", {}),
                        user_id=user_id,
                    )
                    new_version = repo.update_document_version(
                        document_id=existing_doc["id"],
                        embedding=embedding or [],
                        processed_content=processed_text,
                        content_metadata={
                            **parsed["metadata"],
                            "concepts": concepts,
                            "similarity_to_previous": similarity,
                            "language": lang_code,
                            "translated_to_english": bool(translated_by),
                            "translation_model": translated_by,
                            "analytics": analytics,
                        },
                        vector_metadata=vector_metadata,
                        embedding_changed=True,
                    )
                except Exception as exc:
                    logger.error("Error updating document version: %s", exc)
                    results.append({"error": "version update failed", "name": filename})
                    continue

                document = repo.get_document(existing_doc["id"], user_id)
                # Update RAG embedding
                try:
                    if rag_system:
                        rag_system.store_document_embedding(user_id, processed_text, "document", existing_doc["id"], {"name": filename})
                except Exception:
                    logger.warning("RAG embedding update failed", exc_info=True)

                results.append(
                    {
                        **(document or {}),
                        "message": f"File updated to version {new_version}",
                        "reprocessed": True,
                        "version": new_version,
                        "analytics": analytics,
                    }
                )
                continue

            # New file save
            upload_dir = get_upload_directory()
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{user_id}_{timestamp}_{filename}"
            file_path = upload_dir / saved_filename
            with open(file_path, "wb") as f:
                f.write(file_data)

            payload = {
                "user_id": user_id,
                "name": filename,
                "description": description,
                "storage_uri": str(file_path),
                "storage_type": "local",
                "classification": classification,
                "file_type": file_type,
                "file_size_bytes": file_size,
                "original_content": parsed["content"],
                "processed_content": processed_text,
                "content_metadata": {
                    **parsed["metadata"],
                    "concepts": concepts,
                    "language": lang_code,
                    "translated_to_english": bool(translated_by),
                    "translation_model": translated_by,
                    "analytics": analytics,
                },
                "embedding": embedding,
                "vector_metadata": vector_metadata,
                "ollama_model": ollama_model,
                "allow_ai_to_suggest": True,
            }

            document_id = repo.create_data_feed(payload)
            if not document_id:
                results.append({"error": "failed to create document record", "name": filename})
                continue

            # Store in RAG
            try:
                if rag_system:
                    rag_system.store_document_embedding(user_id, processed_text, "document", document_id, {"name": filename})
            except Exception:
                logger.warning("RAG embedding store failed", exc_info=True)

            document = repo.get_document(document_id, user_id)
            results.append(
                {**(document or {}), "message": "File uploaded successfully", "reprocessed": True, "analytics": analytics}
            )

        except Exception as exc:
            logger.error(f"Error uploading file '{file.filename}': {exc}", exc_info=True)
            results.append({"error": "internal server error", "name": file.filename})

    if len(results) == 1:
        result = results[0]
        status = 201 if result.get("id") else 400
        return jsonify(result), status
    return jsonify({"results": results}), 207


@bp.post("/text")
def submit_text():
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "invalid JSON data"}), 400

    text_content = payload.get("content")
    name = payload.get("name", "Text Input")
    if not text_content:
        return jsonify({"error": "content is required"}), 400

    try:
        result = process_text_input(text_content, name)
        if not result["success"]:
            error = result.get("metadata", {}).get("error", "Failed to process text")
            return jsonify({"error": error}), 400

        ollama_service = current_app.config.get("OLLAMA_SERVICE")
        concepts = extract_key_concepts(result["processed_content"], ollama_service)
        embedding = None
        ollama_model = None
        if ollama_service and ollama_service.is_available():
            embedding = ollama_service.generate_embedding(result["processed_content"])
            model_info = ollama_service.get_model_info()
            ollama_model = f"{model_info.get('model_path', 'unknown')}"

        cfg = current_app.config["APP_CONFIG"]
        repo = DocumentsRepository(cfg.database_url, cfg.queries)
        vector_metadata = build_vector_metadata(concepts, embedding)

        doc_payload = {
            "user_id": user_id,
            "name": name,
            "description": payload.get("description", ""),
            "storage_uri": "",
            "storage_type": "text_input",
            "classification": payload.get("classification", "internal"),
            "file_type": "text_input",
            "file_size_bytes": len(result["content"].encode("utf-8")),
            "original_content": result["content"],
            "processed_content": result["processed_content"],
            "content_metadata": {**result["metadata"], "concepts": concepts},
            "embedding": embedding,
            "vector_metadata": vector_metadata,
            "ollama_model": ollama_model,
            "allow_ai_to_suggest": True,
        }

        document_id = repo.create_data_feed(doc_payload)
        if not document_id:
            return jsonify({"error": "failed to create document record"}), 500

        # RAG embedding
        try:
            rag_system = current_app.config.get("RAG_SYSTEM")
            if rag_system:
                rag_system.store_document_embedding(user_id, result["processed_content"], "document", document_id, {"name": name})
        except Exception:
            logger.warning("RAG embedding store failed", exc_info=True)

        document = repo.get_document(document_id, user_id)
        return jsonify(document or {}), 201

    except Exception as exc:
        logger.error(f"Error submitting text: {exc}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500


@bp.get("/<int:document_id>/content")
def get_document_content(document_id: int):
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    content = repo.get_document(document_id, user_id)
    if not content:
        return jsonify({"error": "document not found"}), 404
    return jsonify(content)


from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.utils import secure_filename

from api.repositories.documents_repo import DocumentsRepository
from api.utils.file_processors import process_file, process_text_input, validate_file_size
from api.utils.metadata_extractor import (
    build_vector_metadata,
    extract_key_concepts,
)

logger = logging.getLogger(__name__)

bp = Blueprint("documents", __name__)

ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx'}


def require_auth():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id


@bp.get("")
def list_documents():
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    documents = repo.list_documents(user_id)
    return jsonify({"documents": documents})


@bp.post("")
def create_document():
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "invalid JSON data"}), 400

    required_fields = ["name", "storage_uri"]
    for field in required_fields:
        if not payload.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    payload["user_id"] = user_id
    document_id = repo.create_document(payload)
    if not document_id:
        return jsonify({"error": "failed to create document"}), 500

    document = repo.get_document(document_id, user_id)
    return jsonify(document), 201


@bp.get("/<int:document_id>")
def get_document(document_id: int):
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    doc = repo.get_document(document_id, user_id)
    if not doc:
        return jsonify({"error": "document not found"}), 404
    return jsonify(doc)


@bp.put("/<int:document_id>")
def update_document(document_id: int):
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "invalid JSON data"}), 400

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)

    success = repo.update_document(document_id, user_id, payload)
    if not success:
        return jsonify({"error": "document not found"}), 404

    doc = repo.get_document(document_id, user_id)
    return jsonify(doc)


@bp.delete("/<int:document_id>")
def delete_document(document_id: int):
    """Soft delete a document (keeps data for audit)."""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    # Get optional reason from query parameter or JSON body
    reason = request.args.get("reason")
    if not reason and request.is_json:
        payload = request.get_json(force=True) or {}
        reason = payload.get("reason")

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    success = repo.soft_delete_document(document_id, user_id, reason)
    if not success:
        return jsonify({"error": "document not found"}), 404
    
    return jsonify({
        "message": "document deleted",
        "note": "Document marked as deleted but data preserved for audit"
    })


@bp.post("/<int:document_id>/share-log")
def record_document_share(document_id: int):
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    payload = request.get_json(force=True) or {}
    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)

    session_id = payload.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    log_id = repo.record_share(
        session_id=session_id,
        document_id=document_id,
        recipient_identifier=payload.get("recipient_identifier"),
        channel=payload.get("channel"),
        metadata=payload.get("metadata"),
    )
    return jsonify({"share_log_id": log_id})


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_directory() -> Path:
    """Get or create upload directory for data feeds."""
    upload_dir = Path(
        os.getenv("DATA_FEEDS_UPLOAD_DIR", "backend/uploads/data_feeds")
    )
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@bp.post("/upload")
def upload_file():
    """Upload a file (txt, csv, xlsx) as a data feed with version detection."""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    # Check if file is present
    if 'file' not in request.files:
        return jsonify({"error": "no file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "no file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": f"file type not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400

    try:
        # Read file data
        file_data = file.read()
        file_size = len(file_data)

        # Validate file size
        is_valid, error_msg = validate_file_size(file_size)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Get file details
        filename = secure_filename(file.filename)
        file_type = filename.rsplit('.', 1)[1].lower()

        # Process file
        result = process_file(file_data, filename, file_type)
        if not result["success"]:
            error = result.get("metadata", {}).get("error", "Failed to process file")
            return jsonify({"error": error}), 400

        # Get services
        cfg = current_app.config["APP_CONFIG"]
        repo = DocumentsRepository(cfg.database_url, cfg.queries)
        ollama_service = current_app.config.get("OLLAMA_SERVICE")

        # Check if document with same name already exists
        existing_doc = repo.check_existing_document(filename, user_id)

        # Extract key concepts
        concepts = extract_key_concepts(
            result["processed_content"],
            ollama_service
        )

        # Generate embedding
        embedding = None
        ollama_model = None
        if ollama_service and ollama_service.is_available():
            embedding = ollama_service.generate_embedding(result["processed_content"])
            model_info = ollama_service.get_model_info()
            ollama_model = f"{model_info.get('model_path', 'unknown')}"

        # Build vector metadata
        vector_metadata = build_vector_metadata(concepts, embedding)

        # Get optional fields from form data
        description = request.form.get("description", "")
        classification = request.form.get("classification", "internal")

        # VERSION DETECTION: Check if content changed
        if existing_doc and embedding:
            existing_embedding = existing_doc.get("embedding")
            
            if existing_embedding and ollama_service:
                # Compare embeddings using cosine similarity
                similarity = ollama_service.compare_embeddings(existing_embedding, embedding)
                logger.info(f"Embedding similarity for '{filename}': {similarity:.4f}")
                
                # If similarity > 0.95, content essentially unchanged
                if similarity > 0.95:
                    logger.info(f"File '{filename}' unchanged (similarity {similarity:.4f}), returning existing document")
                    document = repo.get_document(existing_doc["id"], user_id)
                    return jsonify({
                        **document,
                        "message": "File content unchanged, existing document returned",
                        "similarity_score": similarity,
                        "reprocessed": False
                    }), 200
                
                # Content changed - create version snapshot and update
                logger.info(f"File '{filename}' changed (similarity {similarity:.4f}), creating new version")
                
                # Create version snapshot of old version
                repo.create_version_snapshot(
                    document_id=existing_doc["id"],
                    version=existing_doc["version"],
                    embedding=existing_embedding,
                    content_snapshot=result["processed_content"][:1000],  # Snapshot first 1000 chars
                    metadata_snapshot=existing_doc.get("content_metadata", {}),
                    user_id=user_id
                )
                
                # Update document with new version
                new_version = repo.update_document_version(
                    document_id=existing_doc["id"],
                    embedding=embedding,
                    processed_content=result["processed_content"],
                    content_metadata={
                        **result["metadata"],
                        "concepts": concepts,
                        "similarity_to_previous": similarity,
                    },
                    vector_metadata=vector_metadata,
                    embedding_changed=True
                )
                
                document = repo.get_document(existing_doc["id"], user_id)
                return jsonify({
                    **document,
                    "message": f"File updated to version {new_version}",
                    "similarity_score": similarity,
                    "reprocessed": True,
                    "version": new_version
                }), 200

        # New file - save to disk and create document
        upload_dir = get_upload_directory()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        saved_filename = f"{user_id}_{timestamp}_{filename}"
        file_path = upload_dir / saved_filename
        
        with open(file_path, 'wb') as f:
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
            "original_content": result["content"],
            "processed_content": result["processed_content"],
            "content_metadata": {
                **result["metadata"],
                "concepts": concepts,
            },
            "embedding": embedding,
            "vector_metadata": vector_metadata,
            "ollama_model": ollama_model,
            "allow_ai_to_suggest": True,
        }

        document_id = repo.create_data_feed(payload)
        if not document_id:
            return jsonify({"error": "failed to create document record"}), 500

        document = repo.get_document(document_id, user_id)
        return jsonify({
            **document,
            "message": "File uploaded successfully",
            "reprocessed": True
        }), 201

    except Exception as exc:
        logger.error(f"Error uploading file: {exc}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500


@bp.post("/text")
def submit_text():
    """Submit direct text input as a data feed."""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    payload = request.get_json(force=True)
    if not payload:
        return jsonify({"error": "invalid JSON data"}), 400

    # Get required fields
    text_content = payload.get("content")
    name = payload.get("name", "Text Input")

    if not text_content:
        return jsonify({"error": "content is required"}), 400

    try:
        # Process text input
        result = process_text_input(text_content, name)
        if not result["success"]:
            error = result.get("metadata", {}).get("error", "Failed to process text")
            return jsonify({"error": error}), 400

        # Get OLLama service
        ollama_service = current_app.config.get("OLLAMA_SERVICE")

        # Extract key concepts
        concepts = extract_key_concepts(
            result["processed_content"],
            ollama_service
        )

        # Generate embedding
        embedding = None
        ollama_model = None
        if ollama_service and ollama_service.is_available():
            embedding = ollama_service.generate_embedding(result["processed_content"])
            model_info = ollama_service.get_model_info()
            ollama_model = f"{model_info.get('model_path', 'unknown')}"

        # Build vector metadata
        vector_metadata = build_vector_metadata(concepts, embedding)

        # Get optional fields
        description = payload.get("description", "")
        classification = payload.get("classification", "internal")

        # Create document record
        cfg = current_app.config["APP_CONFIG"]
        repo = DocumentsRepository(cfg.database_url, cfg.queries)

        doc_payload = {
            "user_id": user_id,
            "name": name,
            "description": description,
            "storage_uri": "",  # No file stored for text input
            "storage_type": "text_input",
            "classification": classification,
            "file_type": "text_input",
            "file_size_bytes": len(text_content.encode('utf-8')),
            "original_content": result["content"],
            "processed_content": result["processed_content"],
            "content_metadata": {
                **result["metadata"],
                "concepts": concepts,
            },
            "embedding": embedding,
            "vector_metadata": vector_metadata,
            "ollama_model": ollama_model,
            "allow_ai_to_suggest": True,
        }

        document_id = repo.create_data_feed(doc_payload)
        if not document_id:
            return jsonify({"error": "failed to create document record"}), 500

        document = repo.get_document(document_id, user_id)
        return jsonify(document), 201

    except Exception as exc:
        logger.error(f"Error submitting text: {exc}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500


@bp.get("/<int:document_id>/content")
def get_document_content(document_id: int):
    """Retrieve processed content of a document."""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    
    content = repo.get_relevant_content(document_id, user_id)
    if not content:
        return jsonify({"error": "document not found"}), 404
    
    return jsonify(content)


# ===== Phase 2: Soft Deletion Endpoints =====

@bp.post("/<int:document_id>/restore")
def restore_document(document_id: int):
    """Restore a soft-deleted document."""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    
    success = repo.restore_document(document_id, user_id)
    if not success:
        return jsonify({"error": "document not found or not deleted"}), 404
    
    document = repo.get_document(document_id, user_id)
    return jsonify({
        **document,
        "message": "document restored successfully"
    })


@bp.get("/deleted")
def list_deleted_documents():
    """List all soft-deleted documents for the current user."""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    
    deleted_docs = repo.list_deleted_documents(user_id)
    return jsonify({"documents": deleted_docs})


# ===== Phase 2: Version History Endpoints =====

@bp.get("/<int:document_id>/versions")
def get_version_history(document_id: int):
    """Get version history for a document."""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    
    versions = repo.get_version_history(document_id, user_id)
    return jsonify({"versions": versions})


@bp.get("/<int:document_id>/versions/<int:version>")
def get_version_content(document_id: int, version: int):
    """Get content of a specific version."""
    user_id = require_auth()
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    cfg = current_app.config["APP_CONFIG"]
    repo = DocumentsRepository(cfg.database_url, cfg.queries)
    
    version_content = repo.get_version_content(document_id, version, user_id)
    if not version_content:
        return jsonify({"error": "version not found"}), 404
    
    return jsonify(version_content)


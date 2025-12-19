#!/usr/bin/env python
"""
Simple CLI helper to ingest a file, seed the pgvector store, and optionally
run a retrieval + generation round trip. This mirrors the manual commands
we have been using so you can validate the full pipeline with one call.

Example:
    PYTHONPATH=backend pvenv/bin/python backend/scripts/rag_smoke_test.py \
        --file test.csv \
        --user-email test@quell-ai.com \
        --description "Smoke run" \
        --query "What is Alice's age?"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List

from api.utils.config import Config
from api.repositories.users_repo import UsersRepository
from api.repositories.documents_repo import DocumentsRepository
from api.models.ollama_service import OllamaService
from api.models.rag_system import RAGSystem
from scripts.ingest_file import ingest_single_file


def resolve_user_id(cfg: Config, user_id: int, user_email: str | None) -> int:
    """Resolve the user id when an email is provided."""
    if not user_email:
        return user_id
    repo = UsersRepository(cfg.database_url, cfg.queries)
    user = repo.get_user_by_email(user_email)
    if not user:
        raise SystemExit(f"No user found with email {user_email!r}.")
    return int(user["id"])


def build_metadata(document: Dict[str, Any], filename: str) -> Dict[str, Any]:
    base = {
        "filename": document.get("name") or filename,
        "source": "rag_smoke_test",
    }
    content_meta = document.get("content_metadata") or {}
    if "file_hash" in content_meta:
        base["file_hash"] = content_meta["file_hash"]
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed RAG embeddings and optionally run a retrieval smoke test.")
    parser.add_argument("--file", required=True, help="Path to the file to ingest")
    parser.add_argument("--user-id", type=int, default=3, help="Numeric user id (defaults to 3)")
    parser.add_argument("--user-email", default=None, help="Resolve the user by email (overrides --user-id)")
    parser.add_argument("--description", default="RAG smoke test", help="Document description")
    parser.add_argument("--classification", default="internal", help="Document classification label")
    parser.add_argument("--document-type", default="document", help="Document type tag to store in the vector table")
    parser.add_argument("--query", default=None, help="Optional prompt to run after seeding")
    parser.add_argument("--top-k", type=int, default=3, help="Number of matches to retrieve for the query")
    args = parser.parse_args()

    cfg = Config.load()
    user_id = resolve_user_id(cfg, args.user_id, args.user_email)
    file_path = Path(args.file).expanduser().resolve()
    if not file_path.exists():
        raise SystemExit(f"File not found: {file_path}")

    ollama = OllamaService()
    if not ollama.is_available():
        raise SystemExit("Ollama is not available. Please start the service first.")
    rag = RAGSystem(cfg, ollama)

    print(f"[rag-smoke] ingesting {file_path.name} as user {user_id}...")
    ingest_result = ingest_single_file(
        file_path=file_path,
        save=True,
        user_id=user_id,
        description=args.description,
        classification=args.classification,
        ask=None,
        user_email=args.user_email,
    )
    if not ingest_result.get("ok"):
        raise SystemExit(f"Ingestion failed: {ingest_result.get('error')}")

    document = ingest_result.get("document") or {}
    doc_id = document.get("id")
    processed_text = ingest_result.get("processed_content") or ""
    if not processed_text:
        raise SystemExit("Processed content missing from ingest response; cannot seed embedding.")

    metadata = build_metadata(document, file_path.name)
    embedding_id = rag.store_document_embedding(
        user_id=user_id,
        content=processed_text,
        document_type=args.document_type,
        document_id=doc_id,
        metadata=metadata,
    )
    if embedding_id is None:
        raise SystemExit("Failed to store the embedding in pgvector.")
    print(f"[rag-smoke] stored embedding id={embedding_id} for document id={doc_id}")

    if not args.query:
        print("[rag-smoke] done (no query provided).")
        return

    print(f"[rag-smoke] running retrieval for query: {args.query!r}")
    matches = rag.retrieve_similar_documents(
        query=args.query,
        user_id=user_id,
        document_types=[args.document_type],
        limit=max(1, args.top_k),
    )
    if not matches:
        print("[rag-smoke] no documents returned for this query.")
        return

    for idx, doc in enumerate(matches, start=1):
        snippet = (doc.get("content") or "")[:200].replace("\n", " ")
        print(f"[rag-smoke] match {idx}: doc_id={doc.get('document_id')} score={doc.get('similarity_score'):.4f} snippet={snippet!r}")

    context_parts: List[str] = [doc.get("content") or "" for doc in matches if doc.get("content")]
    context = "\n\n---\n\n".join(context_parts)
    if not context.strip():
        print("[rag-smoke] retrieved documents but no textual content to send to the model.")
        return

    answer = ollama.generate_response(query=args.query, context=context)
    print("\n[rak-smoke] model reply:\n")
    print(answer)


if __name__ == "__main__":
    main()

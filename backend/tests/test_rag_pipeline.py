from __future__ import annotations

import os
from pathlib import Path

from api.utils.config import Config
from api.models.ollama_service import OllamaService
from api.models.rag_system import RAGSystem
from scripts.ingest_file import ingest_single_file


cfg = Config.load()
ollama = OllamaService()
print(ollama)
if not ollama.is_available():
    raise SystemExit("Ollama is not running locally.")

rag = RAGSystem(cfg, ollama)
file_path = Path(os.getenv("RAG_TEST_FILE", "/home/john.vimrish01/repository/actual_code/quell-ai/quell-ai/PizzaSales.csv"))
if not file_path.exists():
    raise SystemExit(f"File {file_path} not found.")
user_id = int(os.getenv("RAG_TEST_USER_ID", "3"))

ingest = ingest_single_file(
    file_path=file_path,
    save=False,
    user_id=user_id,
    description="pytest rag smoke",
    classification="internal",
)
if not ingest.get("ok"):
    raise SystemExit(ingest)
processed_text = ingest.get("processed_content") or ""
if not processed_text:
    raise SystemExit("No processed content returned from ingest pipeline.")

metadata = {"filename": file_path.name, "source": "pytest"}
record_id = rag.store_document_embedding(
    user_id=user_id,
    content=processed_text,
    document_type="document",
    metadata=metadata,
)
if record_id is None:
    raise SystemExit("Failed to store embedding")

docs = rag.retrieve_similar_documents(
    query="Rows Count of Pizza_name - John",
    user_id=user_id,
    document_types=["document"],
    limit=1,
)
if not docs:
    raise SystemExit("No matches returned from vector search.")
retrieved = docs[0].get("content") or ""
assert "Hawaiian Pizza" in retrieved
print("Retrieved doc snippet:", retrieved[:200])

context = "\n\n".join(
    f"{(doc.get('document_metadata') or {}).get('filename', 'doc')}:\n{doc.get('content') or ''}"
    for doc in docs
)
response = ollama.generate_response(
    "Rows Count of Pizza_name - John",
    context,
)
print("Ollama reply:", response)

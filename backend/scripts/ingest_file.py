from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


# Ensure 'backend' root (which contains the 'api' package) is importable when running this file directly
THIS_FILE = Path(__file__).resolve()
BACKEND_ROOT = THIS_FILE.parents[1]  # .../backend
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from api.utils.file_processors import process_file, validate_file_size  # noqa: E402
from api.utils.nlp_utils import detect_language, translate_to_english  # noqa: E402
from api.utils.analytics import analyze_text, analyze_table, analyze_json  # noqa: E402
from api.utils.metadata_extractor import build_vector_metadata, extract_key_concepts  # noqa: E402
from api.models.ollama_service import OllamaService  # noqa: E402


def _get_upload_directory() -> Path:
    """Mirror the server's upload directory behavior."""
    upload_dir = Path(os.getenv("DATA_FEEDS_UPLOAD_DIR", "backend/uploads/data_feeds"))
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _serialize_row(row: Any) -> str:
    return " | ".join("" if v is None else str(v) for v in row)


def build_llm_context(
    parsed: Dict[str, Any],
    file_type: str,
    rows_limit: int = 500,
    focus_sheets: Optional[List[str]] = None,
) -> str:
    """Convert parsed data to a textual context for the LLM to reason over.

    - For Excel: include each sheet name, columns, and up to rows_limit rows
    - For CSV: include columns and rows up to rows_limit
    - For JSON: include the JSON string (truncated if very large)
    """
    lines: list[str] = []
    focus_set = set([s.strip().lower() for s in (focus_sheets or [])]) if focus_sheets else set()

    # Excel multi-sheet
    if isinstance(parsed.get("sheets"), list) and parsed["sheets"]:
        sheets = parsed["sheets"]
        # Workbook summary header for the model to understand structure
        lines.append(f"WORKBOOK: {len(sheets)} sheets")
        lines.append(
            "SUMMARY: "
            + "; ".join(
                f"{(s.get('sheet_name') or 'Sheet')} (rows={len(s.get('rows') or [])}, cols={len(s.get('columns') or [])})"
                for s in sheets
            )
        )
        for sheet in sheets:
            name = str(sheet.get("sheet_name", "Sheet"))
            if focus_set and name.strip().lower() not in focus_set:
                continue
            cols = [str(c) for c in (sheet.get("columns") or [])]
            rows = sheet.get("rows") or []
            total = len(rows)
            take = min(rows_limit, total)
            lines.append(f"SHEET: {name}")
            lines.append(f"COLUMNS: {', '.join(cols)}")
            lines.append(f"ROWS (showing {take} of {total}):")
            for r in rows[:take]:
                lines.append(_serialize_row(r))
        return "\n".join(lines)

    # CSV/tabular
    if parsed.get("columns") is not None and parsed.get("rows") is not None:
        cols = [str(c) for c in (parsed.get("columns") or [])]
        rows = parsed.get("rows") or []
        total = len(rows)
        take = min(rows_limit, total)
        lines.append("SHEET: CSV")
        lines.append(f"COLUMNS: {', '.join(cols)}")
        lines.append(f"ROWS (showing {take} of {total}):")
        for r in rows[:take]:
            lines.append(_serialize_row(r))
        return "\n".join(lines)

    # JSON
    if file_type == "json":
        content = parsed.get("content") or ""
        if len(content) > 200000:
            content = content[:200000] + "\n... [truncated]"
        return f"JSON CONTENT START\n{content}\nJSON CONTENT END"

    # Fallback to processed_content text
    return str(parsed.get("processed_content") or "")


def _parse_focus_sheets(ask: str) -> List[str]:
    """Extract sheet names enclosed in single quotes from the ask.
    Example: On sheet 'Employees' ... -> ['Employees']
    """
    if not ask:
        return []
    return [m.strip() for m in re.findall(r"'([^']+)'", ask)]


def _extract_answer_parts(text: Optional[str]) -> Dict[str, Any]:
    """Extract a short 'Answer: ...' line and JSON details from model output.

    Returns { 'answer_short': str|None, 'answer_data': dict|None }
    """
    if not text:
        return {"answer_short": None, "answer_data": None}
    answer_short = None
    m = re.search(r"^\s*Answer\s*:\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
    if m:
        answer_short = m.group(1).strip()

    # Try to find a JSON object in the response
    answer_data = None
    try:
        jmatch = re.search(r"\{[\s\S]*\}", text)
        if jmatch:
            answer_data = json.loads(jmatch.group(0))
    except Exception:
        answer_data = None

    return {"answer_short": answer_short, "answer_data": answer_data}


def _first_json_object(s: str) -> Optional[Dict[str, Any]]:
    try:
        # Prefer exact JSON if the whole string is JSON
        return json.loads(s)
    except Exception:
        pass
    try:
        m = re.search(r"\{[\s\S]*\}", s)
        if m:
            return json.loads(m.group(0))
    except Exception:
        return None
    return None


def _is_structured_query(ask: str) -> bool:
    q = ask.lower()
    # Basic detection for counting/listing tasks with optional sheet scoping
    return ("how many" in q or "count" in q) or ("list" in q and "sheet" in q)


def _format_structured_short(ad: Dict[str, Any]) -> str:
    if not isinstance(ad, dict):
        return ""
    if ad.get("insufficient"):
        return f"insufficient context: {ad.get('reason','')}".strip()
    if "count" in ad:
        sheet = ad.get("sheet")
        return f"count={ad.get('count')}" + (f" on sheet {sheet}" if sheet else "")
    # Generic fallback
    return json.dumps(ad, ensure_ascii=False)


def ingest_single_file(
    file_path: Path,
    save: bool,
    user_id: int,
    description: str,
    classification: str,
    ask: str | None,
    user_email: str | None = None,
) -> Dict[str, Any]:
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = file_path.name
    file_type = file_path.suffix.lower().lstrip(".")
    if file_type not in {"txt", "csv", "xlsx", "json"}:
        raise ValueError(f"Unsupported file type: .{file_type}")

    file_data = file_path.read_bytes()
    is_valid, error_msg = validate_file_size(len(file_data))
    if not is_valid:
        raise ValueError(error_msg or "File too large")

    # Initialize Ollama service directly unless saving requires full app context
    ollama_service = OllamaService(model_path=os.getenv("OLLAMA_MODEL_PATH"))
    repo = None
    app = None
    if save:
        try:
            from api.app import create_app  # type: ignore
            from api.repositories.documents_repo import DocumentsRepository  # type: ignore
            from api.repositories.users_repo import UsersRepository  # type: ignore
            app = create_app()
            with app.app_context():
                cfg = app.config["APP_CONFIG"]
                repo = DocumentsRepository(cfg.database_url, cfg.queries)
                users_repo = UsersRepository(cfg.database_url, cfg.queries)
                # Resolve user by email if provided
                if user_email:
                    u = users_repo.get_user_by_email(user_email)
                    if not u:
                        return {"ok": False, "error": f"No user found with email: {user_email}"}
                    user_id = int(u["id"])  # override with resolved ID
                else:
                    # Validate provided user_id exists
                    if not users_repo.get_user_by_id(int(user_id)):
                        return {
                            "ok": False,
                            "error": (
                                f"User id {user_id} not found. Use --user_id for an existing user or provide --user-email to resolve. "
                                "Alternatively, run backend/api/db/migrations/create_dummy_user.sql to create a test user."
                            ),
                        }
                print('test')
                # Prefer app-managed Ollama if available
                svc = app.config.get("OLLAMA_SERVICE")
                if svc is not None:
                    ollama_service = svc
        except Exception as exc:
            return {"ok": False, "error": f"Failed to initialize app/DB for save: {exc}"}

        # Parse file into normalized text/structures
        parsed = process_file(file_data, filename, file_type)
        if not parsed["success"]:
            error = parsed.get("metadata", {}).get("error", "Failed to process file")
            return {"ok": False, "error": error}

        base_text = parsed.get("processed_content", "")

        # Language detection + translation
        lang_code = detect_language(base_text)
        translated_by = None
        processed_text = base_text
        if lang_code and lang_code not in ("en", "unknown"):
            processed_text, translated_by = translate_to_english(base_text, ollama_service)

        # Analytics
        analytics = {}
        if parsed.get("rows") is not None and parsed.get("columns") is not None:
            analytics = analyze_table(parsed.get("rows", []), parsed.get("columns", []))
        elif file_type == "json":
            analytics = (
                analyze_json(parsed.get("json_data")) if parsed.get("json_data") is not None else {}
            )
        else:
            analytics = analyze_text(processed_text)

        # Concepts and embeddings
        concepts = extract_key_concepts(processed_text, ollama_service)
        embedding = None
        ollama_model = None
        if ollama_service and ollama_service.is_available():
            embedding = ollama_service.generate_embedding(processed_text)
            model_info = ollama_service.get_model_info()
            ollama_model = f"{model_info.get('model_path', 'unknown')}"

        vector_metadata = build_vector_metadata(concepts, embedding)

        # Optional DB persistence
        doc_record: Dict[str, Any] = {}
        if save and repo is not None and app is not None:
            # Save file to disk
            upload_dir = _get_upload_directory()
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{user_id}_{timestamp}_{filename}"
            file_out = upload_dir / saved_filename
            file_out.write_bytes(file_data)

            payload = {
                "user_id": user_id,
                "name": filename,
                "description": description,
                "storage_uri": str(file_out),
                "storage_type": "local",
                "classification": classification,
                "file_type": file_type,
                "file_size_bytes": len(file_data),
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

            doc_id = repo.create_data_feed(payload)
            if doc_id:
                doc_record = repo.get_document(doc_id, user_id) or {}

        # Optional Q&A prompt to the model (LLM-only)
        model_answer = None
        if ask:
            if not (ollama_service and ollama_service.is_available()):
                model_answer = None
            else:
                # Build a richer context directly from the parsed data (restrict to sheet(s) if mentioned)\n                
                focus_sheets = _parse_focus_sheets(ask)
                context = build_llm_context(parsed, file_type, focus_sheets=focus_sheets)
                if _is_structured_query(ask):
                    # Enforce JSON-only output for structured queries
                    query = (
                        "You are a data analyst. Use the provided dataset context strictly to answer. "
                        "If a count or filter is requested, compute it exactly from the rows. "
                        "If the user mentions a sheet in single quotes (e.g. 'Employees'), treat the match as exact and ignore all other sheets. When matching names, build Full Name as First_Name + ' ' + Last_Name and compare for exact equality (case-insensitive, trimmed). When matching City, compare for exact equality (case-insensitive, trimmed). "
                        "Return ONLY a JSON object (no extra text) with keys: count (integer), sheet (string or null), "
                        "criteria (object describing filters you used), and evidence_rows (array of one-line strings, up to 5). "
                        "If the context is insufficient, return {\"insufficient\": true, \"reason\": \"...\"}.\n\n"
                        f"User question: {ask}"
                    )
                    raw = ollama_service.generate_response(query, context)
                    model_answer = raw
                    ad = _first_json_object(raw or "")
                    short = _format_structured_short(ad or {}) if ad else None
                    result_answer_data = ad
                    result_answer_short = short
                else:
                    # Instruction wrapper to guide the LLM to compute precisely.
                    # Ask it to include a short answer line and a JSON details block when possible.
                    query = (
                        "You are a data analyst. Use the provided dataset context strictly to answer. "
                        "If a count or filter is requested, compute it exactly from the rows. "
                        "If the context is truncated and insufficient, say 'insufficient context'. "
                        "If the user mentions a sheet in single quotes (e.g. 'Employees'), treat the match as exact and ignore all other sheets. When matching names, build Full Name as First_Name + ' ' + Last_Name and compare for exact equality (case-insensitive, trimmed). When matching City, compare for exact equality (case-insensitive, trimmed). "
                        "Return two parts if possible: (1) a single line starting with 'Answer: ...', and (2) a JSON object with keys like count, sheet, criteria, and optionally evidence_rows (array).\n\n"
                        f"User question: {ask}"
                    )
                    model_answer = ollama_service.generate_response(query, context)
                    # Extract optional parts
                    parts = _extract_answer_parts(model_answer)
                    result_answer_data = parts.get("answer_data")
                    result_answer_short = parts.get("answer_short")

        return {
            "ok": True,
            "filename": filename,
            "file_type": file_type,
            "language": lang_code,
            "translated_to_english": bool(translated_by),
            "analytics": analytics,
            "concepts": concepts,
            "has_embedding": embedding is not None,
            "saved": bool(doc_record),
            "document": doc_record,
            "model_answer": model_answer,
            "model_answer_short": locals().get("result_answer_short"),
            "model_answer_data": locals().get("result_answer_data"),
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest file(s) into the backend pipeline (parse, translate, analyze, and optionally save)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to .txt/.csv/.xlsx/.json file")
    group.add_argument("--files", nargs="+", help="Multiple file paths (.txt/.csv/.xlsx/.json)")
    parser.add_argument("--save", action="store_true", help="Persist into DB and save a copy under uploads")
    parser.add_argument("--user_id", type=int, default=1, help="User ID for DB record (default: 1)")
    parser.add_argument("--user-email", dest="user_email", default=None, help="Resolve user by email (overrides --user_id)")
    parser.add_argument("--description", default="", help="Optional description for the document")
    parser.add_argument("--classification", default="internal", help="Classification label (default: internal)")
    parser.add_argument("--ask", default=None, help="Ask a question about this file (LLM computes using provided context)")
    parser.add_argument("--rows-limit", type=int, default=500, help="Max rows per sheet to include in LLM context (default: 500)")
    parser.add_argument("--pretty", action="store_true", help="Print a human-readable summary instead of raw JSON")

    args = parser.parse_args()
    result = ingest_single_file(
        file_path=Path(args.file),
        save=args.save,
        user_id=args.user_id,
        description=args.description,
        classification=args.classification,
        ask=args.ask,
        user_email=args.user_email,
    )

    # Output
    if args.pretty and result.get("ok"):
        lines = []
        lines.append(f"File: {result.get('filename')} ({result.get('file_type')})")
        doc = result.get("document") or {}
        if doc:
            lines.append(f"Saved: id={doc.get('id')} | sheets={ (doc.get('content_metadata') or {}).get('sheets_count') }")
        if args.ask:
            short = result.get("model_answer_short")
            lines.append(f"Question: {args.ask}")
            lines.append(f"Answer: {short or (result.get('model_answer') or '').splitlines()[0][:120]}")
            ad = result.get("model_answer_data") or {}
            if ad:
                try:
                    lines.append("Details: " + json.dumps(ad, ensure_ascii=False))
                except Exception:
                    pass
        print("\n".join(lines))
    else:
        import json as _json
        print(_json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()





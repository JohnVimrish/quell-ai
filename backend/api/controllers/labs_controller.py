import base64
import hashlib
import io
import math
import os
import re
import uuid
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.utils import secure_filename

from api.services.labs_pipeline import DEFAULT_EMBED_DIM, LanguagePipelineClient
from api.repositories.temp_user_repo import TempUserRepository
import numpy as np
import soundfile as sf

try:
    from scripts.ingest_file import ingest_single_file
except Exception:  # pragma: no cover - fallback when CLI script unavailable
    ingest_single_file = None  # type: ignore[misc]

bp = Blueprint("labs", __name__)
logger = logging.getLogger(__name__)

TOKEN_LIMIT = 500
CHAR_FALLBACK = 1200
CHAR_OVERLAP = 200
PIPELINE_CLIENT = LanguagePipelineClient.from_env()
EMBED_DIM = PIPELINE_CLIENT.config.embed_dim or DEFAULT_EMBED_DIM
LAB_ALLOWED_EXTENSIONS = {"txt", "csv", "xlsx"}
ASSISTANT_NAME = "Quell-Ai"
DEFAULT_GREETING = "Hello! How can I help you today? To personalize things, may I have your name?"


@dataclass
class Chunk:
    identifier: uuid.UUID
    order: int
    text: str


def _temp_user_repo() -> TempUserRepository:
    repo = current_app.config.get("LAB_TEMP_USER_REPO")
    if repo is None:
        cfg = current_app.config["APP_CONFIG"]
        repo = TempUserRepository(cfg.database_url)
        current_app.config["LAB_TEMP_USER_REPO"] = repo
    return repo


def _ensure_lab_user() -> Dict[str, Any]:
    repo = _temp_user_repo()
    temp_user_id = session.get("lab_temp_user_id")
    if temp_user_id:
        user = repo.get_user(temp_user_id)
        if user:
            return user
    session_id = uuid.uuid4().hex
    user = repo.create_user(session_id)
    session["lab_temp_user_id"] = user.get("id")
    session["lab_temp_session_id"] = user.get("session_id")
    session.setdefault("lab_chat_history", [])
    session.setdefault("lab_uploaded_summaries", [])
    session.modified = True
    return user


def _load_history() -> List[Dict[str, str]]:
    return list(session.get("lab_chat_history", []))


def _save_history(history: List[Dict[str, str]]) -> None:
    session["lab_chat_history"] = history[-10:]
    session.modified = True


def _append_history(role: str, text: str) -> None:
    history = _load_history()
    history.append({"role": role, "text": text})
    _save_history(history)


def _conversation_context() -> str:
    history = _load_history()
    lines = []
    for entry in history[-10:]:
        speaker = "User" if entry.get("role") == "user" else ASSISTANT_NAME
        lines.append(f"{speaker}: {entry.get('text')}")
    return "\n".join(lines).strip()


def _uploads_context() -> str:
    uploads = session.get("lab_uploaded_summaries", [])
    return "\n".join(f"- {summary}" for summary in uploads if summary)


def _record_upload_summary(summary: str) -> None:
    if not summary:
        return
    uploads = list(session.get("lab_uploaded_summaries", []))
    uploads.append(summary)
    session["lab_uploaded_summaries"] = uploads[-5:]
    session.modified = True


def _summarize_ingest_payload(payload: Dict[str, Any]) -> str:
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


@bp.get("/status")
def labs_status() -> Any:
    config = PIPELINE_CLIENT.config
    return jsonify(
        {
            "provider": config.provider,
            "chatModel": config.chat_model,
            "embedModel": config.embed_model,
            "embedDim": EMBED_DIM,
            "hasApiKey": bool(config.api_key),
            "canUseOpenAI": PIPELINE_CLIENT.can_use_openai,
        }
    )


@bp.post("/api-key")
def set_api_key() -> Any:
    payload = request.get_json(silent=True) or {}
    api_key = payload.get("apiKey")
    if not isinstance(api_key, str):
        return jsonify({"error": "apiKey must be provided as a string"}), 400

    api_key = api_key.strip()
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        PIPELINE_CLIENT.config.api_key = api_key
        if PIPELINE_CLIENT.config.provider != "openai":
            PIPELINE_CLIENT.config.provider = "openai"
    else:
        PIPELINE_CLIENT.config.api_key = ""
        os.environ.pop("OPENAI_API_KEY", None)

    return labs_status()


@bp.post("/mcp/run")
def run_multi_component_prompt() -> Any:
    payload = request.get_json(silent=True) or {}
    components = payload.get("components")
    if not isinstance(components, list) or not components:
        return jsonify({"error": "components must be a non-empty list"}), 400

    formatted_parts: List[str] = []
    for index, raw_component in enumerate(components, start=1):
        if isinstance(raw_component, dict):
            label = str(raw_component.get("label") or f"Component {index}").strip()
            content = str(raw_component.get("content") or "").strip()
        else:
            label = f"Component {index}"
            content = str(raw_component).strip()

        if not content:
            continue
        formatted_parts.append(f"[{label}]\n{content}")

    if not formatted_parts:
        return jsonify({"error": "components did not include any content"}), 400

    instructions = str(payload.get("instructions") or "").strip()
    system_prompt = (
        instructions
        or "You are a reasoning assistant. Combine the provided components and deliver a coherent answer."
    )
    user_prompt = "\n\n".join(formatted_parts)

    message_sequence = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response_text = PIPELINE_CLIENT.chat_conversation(
        message_sequence,
        temperature=float(payload.get("temperature", 0.25)),
        max_tokens=int(payload.get("maxTokens", 700)),
    )

    if not response_text:
        response_text = fallback_mcp_response(formatted_parts)

    return jsonify(
        {
            "systemPrompt": system_prompt,
            "combinedPrompt": user_prompt,
            "response": response_text,
            "componentCount": len(formatted_parts),
            "approxTokens": approx_tokens(user_prompt) + approx_tokens(system_prompt),
        }
    )


@bp.post("/chat/session")
def chat_session() -> Any:
    payload = request.get_json(silent=True) or {}
    messages_input = payload.get("messages")
    if not isinstance(messages_input, list) or not messages_input:
        return jsonify({"error": "messages must be a non-empty list"}), 400

    conversation: List[Dict[str, str]] = []
    system_prompt = payload.get("systemPrompt")
    if isinstance(system_prompt, str) and system_prompt.strip():
        conversation.append({"role": "system", "content": system_prompt.strip()})

    for message in messages_input:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        cleaned = content.strip()
        if not cleaned:
            continue
        conversation.append({"role": role, "content": cleaned})

    if not conversation or all(entry["role"] != "user" for entry in conversation):
        return jsonify({"error": "at least one user message is required"}), 400

    reply = PIPELINE_CLIENT.chat_conversation(
        conversation,
        temperature=float(payload.get("temperature", 0.35)),
        max_tokens=int(payload.get("maxTokens", 600)),
    )
    if not reply:
        reply = fallback_chat_response(conversation)

    return jsonify({"reply": reply})


@bp.post("/labs/conversation/session")
def conversation_lab_session() -> Any:
    user = _ensure_lab_user()
    session.setdefault("lab_chat_history", [])
    session.setdefault("lab_uploaded_summaries", [])
    session.modified = True
    return jsonify(
        {
            "userId": user.get("id"),
            "sessionId": user.get("session_id"),
            "assistantName": ASSISTANT_NAME,
            "greeting": DEFAULT_GREETING,
            "hasName": bool(user.get("display_name")),
            "displayName": user.get("display_name"),
        }
    )


@bp.post("/labs/conversation/name")
def conversation_lab_set_name() -> Any:
    user = _ensure_lab_user()
    payload = request.get_json(force=True) or {}
    name = str(payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    user_message = str(payload.get("message") or name).strip()
    if user_message:
        _append_history("user", user_message)

    repo = _temp_user_repo()
    updated = repo.update_name(user["id"], name)
    session["lab_display_name"] = name
    session.modified = True

    ack = f"Great to meet you, {name}! Let me know what you'd like to explore."
    _append_history("assistant", ack)
    return jsonify(
        {
            "ok": True,
            "displayName": updated.get("display_name") if updated else name,
            "assistantReply": ack,
            "assistantName": ASSISTANT_NAME,
        }
    )


@bp.post("/labs/conversation/chat")
def conversation_lab_chat() -> Any:
    user = _ensure_lab_user()
    payload = request.get_json(force=True) or {}
    message = str(payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    _append_history("user", message)

    context_sections: List[str] = []
    uploads_context = _uploads_context()
    if uploads_context:
        context_sections.append("Recent uploads:\n" + uploads_context)
    conversation_context = _conversation_context()
    if conversation_context:
        context_sections.append("Recent chat:\n" + conversation_context)
    context = "\n\n".join(context_sections) or "User is starting a new Conversation Lab session. Respond helpfully and concisely."

    ollama_service = current_app.config.get("OLLAMA_SERVICE")
    if not (ollama_service and ollama_service.is_available()):
        reply = "I'm unable to reach the Quell-Ai model right now. Please try again shortly."
    else:
        reply = ollama_service.generate_response(message, context)

    _append_history("assistant", reply)
    return jsonify(
        {
            "reply": reply,
            "assistantName": ASSISTANT_NAME,
            "displayName": user.get("display_name"),
        }
    )


@bp.post("/labs/conversation/ingest")
def conversation_lab_ingest() -> Any:
    if ingest_single_file is None:
        return jsonify({"error": "ingestion pipeline unavailable"}), 503

    _ensure_lab_user()

    storage = request.files.get("file")
    if storage is None:
        return jsonify({"error": "file is required"}), 400

    original_name = storage.filename or ""
    filename = secure_filename(original_name)
    if not filename:
        return jsonify({"error": "valid filename required"}), 400

    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in LAB_ALLOWED_EXTENSIONS:
        return (
            jsonify(
                {
                    "error": "unsupported file type",
                    "allowed": sorted(LAB_ALLOWED_EXTENSIONS),
                }
            ),
            400,
        )

    file_bytes = storage.read()
    if not file_bytes:
        return jsonify({"error": "file is empty"}), 400

    description = request.form.get("description", "Conversation Lab upload")
    ask = request.form.get("ask")
    user_id = session.get("user_id") or 0

    try:
        result = ingest_single_file(
            file_path=None,
            file_data=file_bytes,
            filename_override=filename,
            save=False,
            user_id=user_id,
            description=description,
            classification="internal",
            ask=ask,
            user_email=None,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("Conversation Lab ingest failed")
        return jsonify({"error": "failed to process file"}), 500

    response_payload = {
        "ok": True,
        "filename": result.get("filename") or filename,
        "fileType": result.get("file_type") or ext,
        "summary": _summarize_ingest_payload(result),
        "language": result.get("language"),
        "analytics": result.get("analytics") or {},
        "concepts": result.get("concepts") or {},
        "translated": bool(result.get("translated_to_english")),
    }
    _record_upload_summary(response_payload["summary"])
    return jsonify(response_payload)


@bp.post("/rag/workbench")
def rag_workbench() -> Any:
    payload = request.get_json(silent=True) or {}
    documents = payload.get("documents")
    query = str(payload.get("query") or "").strip()

    if not isinstance(documents, list) or not documents:
        return jsonify({"error": "documents must be a non-empty list"}), 400
    if not query:
        return jsonify({"error": "query is required"}), 400

    parsed_docs: List[Dict[str, str]] = []
    for index, document in enumerate(documents, start=1):
        if isinstance(document, dict):
            title = str(document.get("title") or document.get("name") or f"Document {index}")
            content = str(document.get("content") or document.get("text") or "")
        else:
            title = f"Document {index}"
            content = str(document or "")

        content = content.strip()
        if content:
            parsed_docs.append({"title": title.strip() or f"Document {index}", "content": content})

    if not parsed_docs:
        return jsonify({"error": "no usable document content was provided"}), 400

    response_payload = rag_from_documents(parsed_docs, query)
    return jsonify(response_payload)


@bp.post("/notebook/respond")
def notebook_respond() -> Any:
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    notes = payload.get("notes") or []
    files = payload.get("files") or []

    documents: List[Dict[str, str]] = []

    if isinstance(notes, list):
        for index, note in enumerate(notes, start=1):
            if isinstance(note, str) and note.strip():
                documents.append({"title": f"Note {index}", "content": note.strip()})

    if isinstance(files, list):
        for uploaded in files:
            if not isinstance(uploaded, dict):
                continue
            name = str(uploaded.get("name") or uploaded.get("filename") or f"File {len(documents) + 1}")
            raw_content = uploaded.get("content")
            encoding = str(uploaded.get("encoding") or uploaded.get("contentEncoding") or "").lower()

            text_content = ""
            if isinstance(raw_content, str):
                if encoding == "base64":
                    try:
                        decoded = base64.b64decode(raw_content.split(",", 1)[-1])
                        text_content = decoded.decode("utf-8", errors="ignore")
                    except Exception:
                        text_content = ""
                else:
                    text_content = raw_content

            if text_content.strip():
                documents.append({"title": name, "content": text_content.strip()})

    if not documents:
        return jsonify({"error": "provide at least one note or file with textual content"}), 400

    response_payload = rag_from_documents(documents, question)
    return jsonify(response_payload)


@bp.post("/chat/speak")
def chat_speak() -> Any:
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400

    audio_bytes, sample_rate = synthesize_placeholder_audio(text)
    audio_base64 = base64.b64encode(audio_bytes).decode("ascii")

    return jsonify(
        {
            "preview": text[:200],
            "audio": audio_base64,
            "sampleRate": sample_rate,
            "contentType": "audio/wav",
            "note": "Generated locally as a placeholder tone. Replace with production TTS as needed.",
        }
    )


@bp.post("/messages/process")
def process_message() -> Any:
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400

    user_lang = (payload.get("userLang") or "en").lower()
    src_lang = (payload.get("srcLang") or "").lower() or None

    detected_lang = detect_language(text)
    source_lang = src_lang or detected_lang

    translated_text = text
    translation_applied = False
    translation_note: Optional[str] = None
    if source_lang != user_lang:
        candidate = translate_text(text, source_lang, user_lang)
        if candidate and candidate != text:
            translated_text = candidate
            translation_applied = True
            translation_note = f"Translated from {source_lang} to {user_lang}"

    chunks, splitter_used = split_text(translated_text, TOKEN_LIMIT, CHAR_FALLBACK, CHAR_OVERLAP)
    summaries = [summarize_chunk(chunk.text) for chunk in chunks]
    final_summary = reduce_summaries(summaries)

    chunk_texts = [chunk.text for chunk in chunks]
    embeddings = embed_many(chunk_texts, EMBED_DIM)
    if not embeddings:
        embeddings = [[0.0] * EMBED_DIM for _ in chunk_texts]

    message_id = persist_pipeline_run(
        source_lang=source_lang,
        user_lang=user_lang,
        raw_text=text,
        final_summary=final_summary,
        chunks=chunks,
        embeddings=embeddings,
    )

    response = {
        "id": str(message_id),
        "finalSummary": final_summary,
        "chunks": [
            {
                "order": chunk.order,
                "summary": summaries[index],
                "text": chunk.text,
            }
            for index, chunk in enumerate(chunks)
        ],
        "steps": {
            "detectedLanguage": detected_lang,
            "sourceLanguage": source_lang,
            "targetLanguage": user_lang,
            "translationApplied": translation_applied,
            "translationNote": translation_note,
            "splitter": splitter_used,
            "chunkCount": len(chunks),
            "pipeline": [
                {"label": "Detect", "detail": f"Detected language: {detected_lang}"},
                {
                    "label": "Translate",
                    "detail": translation_note or "No translation required",
                },
                {"label": "Split", "detail": f"Strategy: {splitter_used}, chunks: {len(chunks)}"},
                {"label": "Summarize", "detail": f"Generated {len(summaries)} chunk summaries"},
            ],
        },
    }
    return jsonify(response)


@bp.post("/images/describe")
def describe_image() -> Any:
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        image_data = payload.get("imageData")
        image_url = payload.get("imageUrl")
        user_lang = (payload.get("userLang") or "en").lower()
        prompt = payload.get("prompt")
    else:
        image_data = None
        image_url = request.form.get("imageUrl")
        user_lang = (request.form.get("userLang") or "en").lower()
        prompt = request.form.get("prompt")
        if "file" in request.files:
            image_file = request.files["file"]
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

    if not image_data and not image_url:
        return jsonify({"error": "imageData or imageUrl is required"}), 400

    caption = describe_image_stub(image_data=image_data, image_url=image_url, user_lang=user_lang, prompt=prompt)
    store_image_stub(image_url=image_url, image_data=image_data, caption=caption)
    return jsonify({"caption": caption})


@bp.get("/search")
def search_chunks() -> Any:
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "query parameter is required"}), 400

    db_manager = current_app.config.get("DB_MANAGER")
    if not db_manager or not db_manager.pool:
        return jsonify({"results": []})

    ensure_schema(db_manager)
    query_embeddings = embed_many([query], EMBED_DIM)
    if not query_embeddings:
        return jsonify({"results": []})
    embedding = query_embeddings[0]
    vector_literal = vector_to_literal(embedding)

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT chunk_id, message_id, ord, text,
                           1 - (embedding <=> %s) AS score
                    FROM ai_intelligence.labs_message_chunks
                    ORDER BY embedding <=> %s
                    LIMIT 5
                    """,
                    (vector_literal, vector_literal),
                )
                rows = cur.fetchall()
    except Exception:  # pragma: no cover - optional integration
        return jsonify({"results": []})

    results = [
        {
            "chunkId": str(row[0]),
            "messageId": str(row[1]),
            "order": row[2],
            "text": row[3],
            "score": float(row[4]) if row[4] is not None else None,
        }
        for row in rows
    ]
    return jsonify({"results": results})


# ---- helpers -----------------------------------------------------------------


def detect_language(text: str) -> str:
    detected = PIPELINE_CLIENT.detect_language(text)
    if detected:
        return detected
    return _fallback_detect_language(text)


def _fallback_detect_language(text: str) -> str:
    sample = text[:200]
    if any('一' <= char <= '鿿' for char in sample):
        return "zh"
    if any('а' <= char.lower() <= 'я' for char in sample):
        return "ru"
    if any(char in "áéíóúñ¿¡" for char in sample):
        return "es"
    if sum(1 for char in sample if char in "éàèçùâêîôû") > 2:
        return "fr"
    return "en"


def translate_text(text: str, src_lang: str, target_lang: str) -> str:
    translated = PIPELINE_CLIENT.translate(text, src_lang, target_lang)
    if translated:
        return translated
    if src_lang == target_lang:
        return text
    return f"[Translated {src_lang}->{target_lang}] {text}"


def split_text(
    text: str,
    token_limit: int,
    char_fallback: int,
    char_overlap: int,
) -> Tuple[List[Chunk], str]:
    chunks = recursive_split(text, token_limit)
    strategy = "recursive"
    if not chunks:
        chunks = char_split(text, char_fallback, char_overlap)
        strategy = "character"
    return chunks, strategy


def recursive_split(text: str, token_limit: int) -> List[Chunk]:
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text) if part.strip()]
    output: List[Chunk] = []
    order = 0

    for paragraph in paragraphs:
        sentences = [s.strip() for s in re.split(r"(?<=[\.\!?])\s+", paragraph) if s.strip()]
        buffer = ""
        for sentence in sentences:
            draft = f"{buffer} {sentence}".strip() if buffer else sentence
            if approx_tokens(draft) > token_limit:
                if buffer:
                    output.append(Chunk(uuid.uuid4(), order, buffer))
                    order += 1
                buffer = sentence
                if approx_tokens(sentence) > token_limit:
                    clauses = [c.strip() for c in re.split(r"[,;:-]\s+", sentence) if c.strip()]
                    clause_buffer = ""
                    for clause in clauses:
                        candidate = f"{clause_buffer}, {clause}".strip(", ") if clause_buffer else clause
                        if approx_tokens(candidate) > token_limit:
                            if clause_buffer:
                                output.append(Chunk(uuid.uuid4(), order, clause_buffer))
                                order += 1
                            clause_buffer = clause
                        else:
                            clause_buffer = candidate
                    if clause_buffer:
                        output.append(Chunk(uuid.uuid4(), order, clause_buffer))
                        order += 1
                    buffer = ""
            else:
                buffer = draft
        if buffer:
            output.append(Chunk(uuid.uuid4(), order, buffer))
            order += 1
    return output


def char_split(text: str, size: int, overlap: int) -> List[Chunk]:
    if not text:
        return []
    output: List[Chunk] = []
    index = 0
    order = 0
    length = len(text)
    while index < length:
        end = min(index + size, length)
        output.append(Chunk(uuid.uuid4(), order, text[index:end]))
        order += 1
        if end == length:
            break
        index = max(end - overlap, 0)
    return output


def summarize_chunk(text: str) -> str:
    summary = PIPELINE_CLIENT.summarize_chunk(text)
    if summary:
        return summary
    return _fallback_summarize_chunk(text)


def _fallback_summarize_chunk(text: str) -> str:
    sentences = [s.strip() for s in re.split(r"(?<=[\.\!?])\s+", text) if s.strip()]
    bullets: List[str] = []
    for sentence in sentences[:3]:
        if len(sentence) > 120:
            sentence = sentence[:117].rstrip() + "..."
        bullets.append(f"- {sentence}")
    if not bullets:
        snippet = text[:120] + "..." if len(text) > 120 else text
        bullets.append(f"- {snippet}")
    return "\n".join(bullets)


def reduce_summaries(summaries: List[str]) -> str:
    reduced = PIPELINE_CLIENT.reduce_summaries(summaries)
    if reduced:
        return reduced
    return _fallback_reduce_summaries(summaries)


def _fallback_reduce_summaries(summaries: List[str]) -> str:
    joined: List[str] = []
    for summary in summaries:
        for line in summary.splitlines():
            clean = line.lstrip("- ").strip()
            if clean:
                joined.append(clean)
    unique: List[str] = []
    seen = set()
    for line in joined:
        if line not in seen:
            unique.append(line)
            seen.add(line)
        if len(unique) == 4:
            break
    return "; ".join(unique) if unique else "No salient points detected."


def approx_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def embed_many(texts: List[str], dim: int) -> List[List[float]]:
    result = PIPELINE_CLIENT.embed_many(texts)
    if result:
        return result
    return _fallback_embed_many(texts, dim)


def rag_from_documents(documents: List[Dict[str, str]], query: str) -> Dict[str, Any]:
    doc_texts = [doc["content"] for doc in documents]
    doc_titles = [doc["title"] for doc in documents]

    doc_embeddings = embed_many(doc_texts, EMBED_DIM)
    query_embedding_list = embed_many([query], EMBED_DIM)

    similarities = np.zeros(len(documents), dtype=float)
    if query_embedding_list:
        query_vec = np.asarray(query_embedding_list[0], dtype=float)
        doc_matrix = np.asarray(doc_embeddings, dtype=float)
        query_norm = np.linalg.norm(query_vec) or 1e-9
        doc_norms = np.linalg.norm(doc_matrix, axis=1)
        denominator = np.clip(doc_norms * query_norm, 1e-9, None)
        similarities = (doc_matrix @ query_vec) / denominator

    ranked = sorted(
        [
            {
                "title": doc_titles[index],
                "content": doc_texts[index],
                "score": float(similarities[index]) if np.isfinite(similarities[index]) else 0.0,
            }
            for index in range(len(documents))
        ],
        key=lambda entry: entry["score"],
        reverse=True,
    )

    context_block = "\n\n".join(
        f"{entry['title']}:\n{entry['content'][:1500]}"
        for entry in ranked[:3]
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a retrieval QA assistant. Answer using only the supplied context. "
                "If the context does not contain the answer, say you cannot find it."
            ),
        },
        {"role": "user", "content": f"Context:\n{context_block}\n\nQuestion: {query}"},
    ]

    answer = PIPELINE_CLIENT.chat_conversation(messages, temperature=0.2, max_tokens=500)
    if not answer:
        answer = fallback_rag_answer(query, ranked[:3])

    return {
        "matches": [
            {
                "title": entry["title"],
                "score": round(entry["score"], 4),
                "preview": entry["content"][:320],
            }
            for entry in ranked[:5]
        ],
        "answer": answer,
        "contextUsed": context_block,
    }


def _fallback_embed_many(texts: List[str], dim: int) -> List[List[float]]:
    embeddings: List[List[float]] = []
    for text in texts:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values = [((seed[i % len(seed)] / 255.0) * 2 - 1) for i in range(dim)]
        embeddings.append([round(val, 6) for val in values])
    return embeddings


def fallback_rag_answer(question: str, matches: List[Dict[str, Any]]) -> str:
    if not matches:
        return "I could not locate relevant context for that question."
    highlights = []
    for match in matches:
        snippet = match["content"][:160].replace("\n", " ").strip()
        highlights.append(f"{match['title']}: {snippet}...")
    joined = " ".join(highlights)
    return f"Based on available notes, here is what I found about \"{question}\": {joined}"


def fallback_mcp_response(components: List[str]) -> str:
    bullet_points = []
    for component in components:
        first_line = component.splitlines()[0] if component else ""
        clean = first_line.strip("[] ")
        if clean:
            bullet_points.append(f"- {clean}")
        if len(bullet_points) == 4:
            break
    if not bullet_points:
        return "Components received. Provide an OpenAI API key to generate a richer response."
    return "Here is a quick synthesis:\n" + "\n".join(bullet_points)


def fallback_chat_response(messages: List[Dict[str, str]]) -> str:
    last_user = next((msg for msg in reversed(messages) if msg["role"] == "user"), None)
    if not last_user:
        return "Hello! I'm ready once you share a question."
    prompt = last_user["content"]
    if len(prompt) > 200:
        prompt = prompt[:197] + "..."
    return f"I received: \"{prompt}\". Add an OpenAI API key to unlock a full assistant response."


def synthesize_placeholder_audio(text: str, sample_rate: int = 16000) -> Tuple[bytes, int]:
    duration = min(6.0, 1.5 + len(text) / 60.0)
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    base_freq = 220 + (len(text) % 160)
    modulation = np.sin(2 * np.pi * 3 * t)
    waveform = 0.25 * np.sin(2 * np.pi * base_freq * t + 0.4 * modulation)
    buffer = io.BytesIO()
    sf.write(buffer, waveform, sample_rate, format="WAV")
    buffer.seek(0)
    return buffer.read(), sample_rate


def vector_to_literal(vector: List[float]) -> str:
    return "[" + ", ".join(f"{value:.6f}" for value in vector) + "]"


def describe_image_stub(
    image_data: Optional[str],
    image_url: Optional[str],
    user_lang: str,
    prompt: Optional[str],
) -> str:
    base_caption = "Image containing discernible objects."
    if image_data:
        try:
            decoded = base64.b64decode(image_data.split(",", 1)[-1])
            approx_kb = max(1, len(decoded) // 1024)
            base_caption = f"Image uploaded (~{approx_kb} KB)."
        except Exception:
            base_caption = "Image uploaded."
    elif image_url:
        base_caption = f"Image at {image_url}."

    if prompt:
        base_caption += f" Prompt focus: {prompt.strip()}"

    if user_lang != "en":
        base_caption = f"[{user_lang}] {base_caption}"
    return base_caption


def store_image_stub(image_url: Optional[str], image_data: Optional[str], caption: str) -> None:
    db_manager = current_app.config.get("DB_MANAGER")
    if not db_manager or not db_manager.pool:
        return
    ensure_schema(db_manager)

    embeddings = embed_many([caption], EMBED_DIM)
    if not embeddings:
        return
    vector_literal = vector_to_literal(embeddings[0])

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_intelligence.labs_images (image_id, convo_id, user_id, url, caption, embedding)
                    VALUES (%s, NULL, NULL, %s, %s, %s)
                    """,
                    (str(uuid.uuid4()), image_url, caption, vector_literal),
                )
                conn.commit()
    except Exception:  # pragma: no cover - optional integration
        return


def persist_pipeline_run(
    source_lang: str,
    user_lang: str,
    raw_text: str,
    final_summary: str,
    chunks: List[Chunk],
    embeddings: List[List[float]],
) -> uuid.UUID:
    message_id = uuid.uuid4()
    db_manager = current_app.config.get("DB_MANAGER")
    if not db_manager or not db_manager.pool:
        return message_id

    ensure_schema(db_manager)

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_intelligence.labs_messages (message_id, convo_id, user_id, source_lang, target_lang, raw_text, final_summary)
                    VALUES (%s, NULL, NULL, %s, %s, %s, %s)
                    """,
                    (str(message_id), source_lang, user_lang, raw_text, final_summary),
                )

                for chunk, embedding in zip(chunks, embeddings):
                    vector_literal = vector_to_literal(embedding)
                    cur.execute(
                        """
                        INSERT INTO ai_intelligence.labs_message_chunks (chunk_id, message_id, ord, text, embedding)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (str(chunk.identifier), str(message_id), chunk.order, chunk.text, vector_literal),
                    )
            conn.commit()
    except Exception:  # pragma: no cover - optional integration
        return message_id

    return message_id


_schema_ready = False


def ensure_schema(db_manager) -> None:
    global _schema_ready
    if _schema_ready:
        return
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ai_intelligence.labs_messages (
                        message_id UUID PRIMARY KEY,
                        convo_id UUID,
                        user_id BIGINT REFERENCES user_management.users(id) ON DELETE SET NULL,
                        source_lang TEXT,
                        target_lang TEXT,
                        raw_text TEXT NOT NULL,
                        final_summary TEXT,
                        created_at TIMESTAMPTZ DEFAULT now()
                    );
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS ai_intelligence.labs_message_chunks (
                        chunk_id UUID PRIMARY KEY,
                        message_id UUID REFERENCES ai_intelligence.labs_messages(message_id) ON DELETE CASCADE,
                        ord INTEGER,
                        text TEXT NOT NULL,
                        embedding vector({EMBED_DIM})
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_labs_messages_user
                        ON ai_intelligence.labs_messages(user_id);
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_labs_message_chunks_message
                        ON ai_intelligence.labs_message_chunks(message_id);
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_labs_message_chunks_embed
                        ON ai_intelligence.labs_message_chunks USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 50);
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS ai_intelligence.labs_images (
                        image_id UUID PRIMARY KEY,
                        convo_id UUID,
                        user_id BIGINT REFERENCES user_management.users(id) ON DELETE SET NULL,
                        url TEXT,
                        caption TEXT,
                        embedding vector({EMBED_DIM}),
                        created_at TIMESTAMPTZ DEFAULT now()
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_labs_images_embed
                        ON ai_intelligence.labs_images USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 25);
                    """
                )
            conn.commit()
        _schema_ready = True
    except Exception:  # pragma: no cover - optional integration
        _schema_ready = False

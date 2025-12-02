import base64
import hashlib
import io
import json
import math
import os
import re
import uuid
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.utils import secure_filename
from sqlalchemy import func

from api.services.labs_pipeline import DEFAULT_EMBED_DIM, LanguagePipelineClient
from api.services.labs_ingest import (
    serialize_ingest_row,
    store_embedding_for_upload,
    summarize_ingest_payload,
)
from api.repositories.temp_user_repo import TempUserRepository
from api.db.vector_store import ConversationLabIngest, ConversationLabMemory
from scripts.ingest_file import ingest_single_file
import numpy as np
import soundfile as sf

bp = Blueprint("labs", __name__)
logger = logging.getLogger(__name__)

TOKEN_LIMIT = 500
CHAR_FALLBACK = 1200
CHAR_OVERLAP = 200
PIPELINE_CLIENT = LanguagePipelineClient.from_env()
EMBED_DIM = PIPELINE_CLIENT.config.embed_dim or DEFAULT_EMBED_DIM
LAB_ALLOWED_EXTENSIONS = {"txt", "csv", "xlsx", "json"}
ASSISTANT_NAME = "Quell-Ai"
DEFAULT_GREETING = "Hello! How can I help you today? To personalize things, may I have your name?"
ASSISTANT_BEHAVIOR = (
        f'''You are Quell-Ai, a friendly and knowledgeable data assistant inside the Conversation Lab.

        You help users analyze, interpret, and reason through data they've uploaded (CSV, Excel, JSON). You behave like a collaborative peer — supportive, concise, and proactive.

        When files are uploaded:
        - Treat them as pandas-style DataFrames or structured documents.
        - Use summaries and retrieved excerpts as trusted sources.
        - Perform joins, filters, group-bys, aggregations, or comparisons as needed.
        - Always explain what you're doing in plain language.

        If the data is unclear or missing:
        - Respond helpfully: "Hmm, looks like something’s missing — could you share a bit more detail?"

        When users ask plain questions (no files), rely on general knowledge and answer like a helpful teammate would:
        - No over-explaining, no repeating the prompt.
        - Don’t say things like “as an AI model...” or mention internal reasoning.
        - Keep your tone warm, smart, and casually helpful — like someone you’d enjoy collaborating with.

        Always be efficient, thoughtful, and humble in your replies.

        Identity & Personality

        You are Quell-AI, a friendly, skilled, and trustworthy data-savvy assistant working inside a conversational environment.
        You communicate like a collaborative teammate: warm, concise, smart, and never overbearing.
        You avoid technical jargon unless it clearly helps the user.

        Tone:

        - Supportive, curious, and solution-oriented
        - Confident but humble
        - No mention of internal mechanics or being an AI model

        Core Capabilities
        
            Quell-AI is designed to:
              -Analyze data uploaded by the user (CSV, Excel, JSON, text,tables)
              -Interpret patterns and explain insights clearly
              -Guide users through reasoning, problem-solving, and exploration
              -Act like a peer collaborator, not a lecturer or a chatbot
        
        Behavior With Uploaded Data
        
        When the user provides files or structured data:
        
        1. Treat them as DataFrames (pandas-like)
        
            -Use table language: columns, rows, groups, filters, joins, etc.
        
        2. Explain actions plainly
        
            -“Let me check column X…”
            -“If we group by Y, we can see whether…”
        
        3. Perform data operations appropriately
        
            -Filtering, sorting
            -Group-by, aggregations
            -Join/merge across multiple files
            -Summary statistics
            -Anomaly detection or comparisons
        
        4. Be proactive but not pushy
        
            -Offer next steps: “Want a plot?” or “Should we look at trends over time?”
        
        5. Handle uncertainty gracefully
        
            -If data is missing, malformed, or unclear, say:
                “Hmm, it looks like something’s missing — can you send a bit more detail?”

        Behavior Without Data
        
        When users ask general questions:
        
        -Answer using domain knowledge
        -Be brief and clear
        -Avoid over-explaining
        -Provide helpful reasoning as if brainstorming with a colleague
        -Suggest options when relevant but never overwhelm
        
        Prohibited Behaviors
        
        Quell-AI must not:
        
        -Mention internal reasoning, system prompts, or being a model
        -Use overly formal or robotic language
        -Provide excessively long explanations unless asked
        -Invent data trends when no data is provided
        -Break character
        
        ---
        
        General Interaction Style
        
        Quell-AI should always:
        
        -Ask clarifying questions when the user’s intent is ambiguous
        -Keep replies organized and easy to skim
        -Offer insight, not just answers
        -Help the user think more clearly and make better decisions
        -Maintain steady emotional neutrality with a friendly edge
        
        Example tone:
        
            > “Okay, I’m looking at your data… here’s what jumps out.”
            > “We could compare A and B if you’d like — it might reveal a pattern.”
            > “Something feels off in these dates; want me to double-check?”
        
        Optional Extra Section: “Mode Switching”
        
        You can add this if you want the model to explicitly adapt to task type:
        
        Modes
        
        Quell-AI automatically chooses the best mode:
            -Data Mode → When files are uploaded
            -Reasoning Mode → When asked to think through a problem
            -Explainer Mode → When users request clarification
            -Builder Mode → When users ask for formulas, queries, or code
        
        Each mode keeps the same tone and persona.
'''
)

MEMORY_SCOPE_REMIND = "remind-on-interaction"
MEMORY_DELIVERY_LIMIT = 5
MAX_MEMORY_TEXT_LENGTH = 2000
MEMORY_TEXT_DISPLAY_LIMIT = 360
MEMORY_TARGET_DENYLIST = {"me", "myself", "you", "yourself", "him", "her", "them", "us", "everyone", "anyone", "somebody"}
MEMORY_COMMAND_PREFIX = re.compile(
    r"^\s*(?:(?:hi|hello|hey)\s+)?(?:(?:quell(?:-|\s)*ai|quell)[:,]?\s*)?(?:please\s+)?(?:(?:can|could|would)\s+you\s+)?(save|remember|tell|remind|let)\b",
    re.IGNORECASE,
)


class InMemoryTempRepo:
    """Fallback temp-user repo when DATABASE_URL is unavailable."""

    def __init__(self):
        self._data: Dict[int, Dict[str, Any]] = {}
        self._counter = 0

    def create_user(
        self,
        session_id: str,
        *,
        display_name: Optional[str] = None,
        ip_hint: Optional[str] = None,
    ) -> Dict[str, Optional[str]]:
        self._counter += 1
        entry = {
            "id": self._counter,
            "session_id": session_id,
            "display_name": display_name,
            "ip_hint": ip_hint,
        }
        self._data[self._counter] = entry
        return entry

    def get_user(self, user_id: int) -> Optional[Dict[str, Optional[str]]]:
        return self._data.get(user_id)

    def update_name(self, user_id: int, display_name: str) -> Optional[Dict[str, Optional[str]]]:
        entry = self._data.get(user_id)
        if entry is None:
            return None
        entry["display_name"] = display_name
        return entry


@dataclass
class Chunk:
    identifier: uuid.UUID
    order: int
    text: str


def _temp_user_repo() -> TempUserRepository:
    repo = current_app.config.get("LAB_TEMP_USER_REPO")
    if repo is None:
        cfg = current_app.config["APP_CONFIG"]
        if not getattr(cfg, "database_url", None):
            repo = current_app.config.get("LAB_TEMP_USER_INMEM")
            if repo is None:
                repo = InMemoryTempRepo()
                current_app.config["LAB_TEMP_USER_INMEM"] = repo
        else:
            repo = TempUserRepository(cfg.database_url)
        current_app.config["LAB_TEMP_USER_REPO"] = repo
    return repo


def _rate_limit(bucket: str, limit: int, window_seconds: int) -> bool:
    """Simple session-based rate limiter. Returns True if blocked."""
    now = time.time()
    store: Dict[str, List[float]] = session.setdefault("lab_rate_limits", {})  # type: ignore[assignment]
    hits = [ts for ts in store.get(bucket, []) if now - ts < window_seconds]
    if len(hits) >= limit:
        store[bucket] = hits
        session["lab_rate_limits"] = store
        session.modified = True
        return True
    hits.append(now)
    store[bucket] = hits
    session["lab_rate_limits"] = store
    session.modified = True
    return False


def _ensure_lab_user() -> Dict[str, Any]:
    repo = _temp_user_repo()
    temp_user_id = session.get("lab_temp_user_id")
    if temp_user_id:
        user = repo.get_user(temp_user_id)
        if user:
            if user.get("display_name"):
                session["lab_display_name"] = user.get("display_name")
            return user
    session_id = uuid.uuid4().hex
    ip_hint = request.headers.get("X-Forwarded-For", request.remote_addr)
    user = repo.create_user(session_id, ip_hint=ip_hint)
    session["lab_temp_user_id"] = user.get("id")
    session["lab_temp_session_id"] = user.get("session_id")
    session.setdefault("lab_chat_history", [])
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


def _get_ingest_rows(
    session_id: Optional[str],
    user_id: int,
    limit: int = 20,
    statuses: Optional[List[str]] = None,
) -> List[ConversationLabIngest]:
    rag = current_app.config.get("RAG_SYSTEM")
    if not (rag and session_id):
        return []
    try:
        query = rag.session.query(ConversationLabIngest).filter(
            ConversationLabIngest.session_id == session_id,
            ConversationLabIngest.user_id == user_id,
        )
        if statuses:
            query = query.filter(ConversationLabIngest.status.in_(statuses))
        return (
            query.order_by(ConversationLabIngest.queued_at.desc())
            .limit(limit)
            .all()
        )
    except Exception as exc:
        try:
            rag.session.rollback()
        except Exception:
            pass
        if hasattr(rag, "reset_session"):
            try:
                rag.reset_session()  # type: ignore[attr-defined]
            except Exception:
                pass
        logger.error("Failed to fetch ingest rows: %s", exc)
        return []


def _clean_memory_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    normalized = re.sub(r"\s+", " ", raw_text).strip()
    return normalized


def _clean_target_name(raw_name: str) -> str:
    if not raw_name:
        return ""
    sanitized = re.sub(r"[^A-Za-z0-9\s'’.-@]", " ", raw_name)
    sanitized = sanitized.replace("@", " ")
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" \"'.,!?")
    if sanitized.lower().endswith(("'s", "’s")) and len(sanitized) > 2:
        sanitized = sanitized[:-2]
    return sanitized.strip()


def _parse_memory_instruction(message: str) -> Optional[Dict[str, str]]:
    if not message:
        return None
    normalized = message.strip()
    if not normalized:
        return None

    # Try to locate a target after a directive verb.
    target_match = re.search(
        r"(?:save\s+|remember\s+|tell\s+|remind\s+|let\s+)(?P<target>[A-Za-z][\w\s'’.-]{0,48})(?:\s+(?:know|that|about))?",
        normalized,
        flags=re.IGNORECASE,
    ) or re.search(
        r"(?:for\s+|to\s+)(?P<target>[A-Za-z][\w\s'’.-]{0,48})(?:\s+(?:know|that|about))?",
        normalized,
        flags=re.IGNORECASE,
    )
    if not target_match:
        return None

    target_name = _clean_target_name(target_match.group("target"))
    if not target_name or target_name.lower() in MEMORY_TARGET_DENYLIST or len(target_name) < 2:
        return None

    # Capture the remainder as the memory body.
    tail = normalized[target_match.end():].strip()
    tail = re.sub(r"^(that|about|regarding)\s+", "", tail, flags=re.IGNORECASE)
    tail = tail.lstrip(":,-–— ").strip()
    memory_text = _clean_memory_text(tail)
    if not memory_text:
        return None
    if len(memory_text) > MAX_MEMORY_TEXT_LENGTH:
        memory_text = memory_text[: MAX_MEMORY_TEXT_LENGTH - 3].rstrip() + "..."
    return {
        "target_name": target_name,
        "memory_text": memory_text,
        "scope": MEMORY_SCOPE_REMIND,
    }


def _store_instructional_memory(user: Dict[str, Any], payload: Dict[str, str]) -> bool:
    rag = current_app.config.get("RAG_SYSTEM")
    if not rag:
        return False
    target_name = payload.get("target_name", "").strip()
    memory_text = payload.get("memory_text", "").strip()
    if not target_name or not memory_text:
        return False
    source_name = session.get("lab_display_name") or user.get("display_name")
    try:
        source_id_raw = user.get("id")
        source_user_id = int(source_id_raw) if source_id_raw else None
    except (TypeError, ValueError):
        source_user_id = None
    entry = ConversationLabMemory(
        source_user_id=source_user_id,
        source_session_id=session.get("lab_temp_session_id"),
        source_display_name=source_name,
        target_name=target_name,
        memory_text=memory_text,
        instruction_scope=payload.get("scope") or MEMORY_SCOPE_REMIND,
    )
    try:
        rag.session.add(entry)
        rag.session.commit()
        return True
    except Exception as exc:
        try:
            rag.session.rollback()
        except Exception:
            pass
        if hasattr(rag, "reset_session"):
            try:
                rag.reset_session()  # type: ignore[attr-defined]
            except Exception:
                pass
        logger.error("Failed to store Conversation Lab memory: %s", exc)
        return False


def _candidate_target_keys(display_name: str) -> List[str]:
    cleaned = _clean_target_name(display_name)
    if not cleaned:
        return []
    lowered = cleaned.lower()
    candidates = [lowered]
    first_word = lowered.split(" ", 1)[0]
    if first_word and first_word not in candidates:
        candidates.append(first_word)
    return candidates


def _format_memory_delivery(memory: ConversationLabMemory, display_name: Optional[str]) -> str:
    target = _clean_target_name(display_name or "") or _clean_target_name(memory.target_name or "")
    if not target:
        target = "there"
    source = memory.source_display_name or "someone else"
    snippet = _clean_memory_text(memory.memory_text or "")
    if len(snippet) > MEMORY_TEXT_DISPLAY_LIMIT:
        snippet = snippet[: MEMORY_TEXT_DISPLAY_LIMIT - 3].rstrip() + "..."
    if snippet and not re.match(r"^[\"“].*[\"”]$", snippet):
        snippet = f"\"{snippet}\""
    return f"Hey {target}, quick heads-up — {source} asked me to pass along: {snippet}."


def _pop_pending_memories(display_name: Optional[str]) -> List[Dict[str, Any]]:
    if not display_name:
        return []
    rag = current_app.config.get("RAG_SYSTEM")
    if not rag:
        return []
    candidates = _candidate_target_keys(display_name)
    if not candidates:
        return []
    try:
        rows = (
            rag.session.query(ConversationLabMemory)
            .filter(
                ConversationLabMemory.delivered.is_(False),
                func.lower(ConversationLabMemory.instruction_scope) == MEMORY_SCOPE_REMIND,
                func.lower(ConversationLabMemory.target_name).in_(candidates),
            )
            .order_by(ConversationLabMemory.created_at.asc())
            .limit(MEMORY_DELIVERY_LIMIT)
            .all()
        )
    except Exception as exc:
        try:
            rag.session.rollback()
        except Exception:
            pass
        logger.error("Failed to load pending Conversation Lab memories: %s", exc)
        return []
    if not rows:
        return []
    now = datetime.utcnow()
    payloads: List[Dict[str, Any]] = []
    for row in rows:
        row.delivered = True
        row.delivered_at = now
        payloads.append(
            {
                "id": row.id,
                "text": _format_memory_delivery(row, display_name),
                "sourceDisplayName": row.source_display_name,
                "createdAt": row.created_at.isoformat() if row.created_at else None,
            }
        )
    try:
        rag.session.commit()
    except Exception as exc:
        try:
            rag.session.rollback()
        except Exception:
            pass
        logger.error("Failed to mark Conversation Lab memories delivered: %s", exc)
        return []
    for entry in payloads:
        _append_history("assistant", entry["text"])
    return payloads


def _normalize_llm_reply(raw_reply: Any) -> str:
    """Convert various LLM reply formats (plain or JSON) into clean text."""

    def _prettify_text(text: str) -> str:
        """Ensure numbered/bulleted lists render on their own lines for the UI."""
        if not text:
            return ""
        normalized = text.replace("\r\n", "\n")
        normalized = re.sub(r"\*\*(.*?)\*\*", r"\1", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)

        def _insert_breaks(pattern: str, value: str) -> str:
            return re.sub(
                pattern,
                lambda match: f"\n{match.group(1)} ",
                value,
            )

        normalized = _insert_breaks(r"(?<!^)(?<!\n)\s*(\d+\.)\s+", normalized)
        normalized = _insert_breaks(r"(?<!^)(?<!\n)\s*([-*•])\s+", normalized)
        normalized = re.sub(r"\n\s+", "\n", normalized)
        return normalized.strip()

    def _extract_text_from_json(payload: Any) -> str:
        if payload is None:
            return ""
        if isinstance(payload, str):
            return payload.strip()
        if isinstance(payload, (int, float)):
            return str(payload)
        if isinstance(payload, bool):
            return "true" if payload else "false"
        if isinstance(payload, dict):
            priority_keys = ("answer", "response", "output", "content", "text", "message")
            for key in priority_keys:
                if key in payload:
                    text = _extract_text_from_json(payload[key])
                    if text:
                        return text
            fragments = []
            for value in payload.values():
                text = _extract_text_from_json(value)
                if text:
                    fragments.append(text)
            return "\n\n".join(fragments)
        if isinstance(payload, (list, tuple, set)):
            fragments = []
            for item in payload:
                text = _extract_text_from_json(item)
                if text:
                    fragments.append(text)
            return "\n\n".join(fragments)
        return str(payload).strip()

    if raw_reply is None:
        return "I'm not sure how to respond right now. Could you please try again?"

    if isinstance(raw_reply, (dict, list, tuple, set)):
        parsed_text = _extract_text_from_json(raw_reply).strip()
        if parsed_text:
            return _prettify_text(parsed_text)
        try:
            return json.dumps(raw_reply, ensure_ascii=False)
        except Exception:
            return _prettify_text(str(raw_reply))

    text_reply = str(raw_reply).strip()
    if not text_reply:
        return "I'm not sure how to respond right now. Could you please try again?"

    if text_reply[0] in "{[":
        try:
            parsed = json.loads(text_reply)
        except Exception:
            return text_reply
        parsed_text = _extract_text_from_json(parsed).strip()
        return _prettify_text(parsed_text or text_reply)

    return _prettify_text(text_reply)


def _uploads_context(limit: int = 3, rows: Optional[List[ConversationLabIngest]] = None) -> str:
    if rows is None:
        session_id = session.get("lab_temp_session_id")
        user_id = int(session.get("lab_temp_user_id") or 0)
        rows = _get_ingest_rows(session_id, user_id, limit=limit, statuses=["ready"])
    if not rows:
        return ""
    snippets = []
    for row in rows:
        metadata = row.ingest_metadata or {}
        summary = metadata.get("summary") or ""
        preview = metadata.get("processed_preview") or ""
        body = summary or preview[:240]
        if not body:
            continue
        snippets.append(f"{row.filename}:\n{body}")
    return "\n\n".join(snippets)


def _pending_ingest_count(session_id: Optional[str], user_id: int) -> int:
    return len(_get_ingest_rows(session_id, user_id, limit=50, statuses=["queued", "processing"]))


def _build_upload_context(
    prompt: str,
    user_id: int,
    session_id: Optional[str],
    ready_rows: Optional[List[ConversationLabIngest]] = None,
) -> str:
    limit = 3
    if ready_rows is None:
        ready_rows = _get_ingest_rows(session_id, user_id, limit=limit, statuses=["ready"])
    if not ready_rows:
        return ""
    rag = current_app.config.get("RAG_SYSTEM")
    if rag:
        try:
            docs = rag.retrieve_similar_documents(
                prompt,
                user_id,
                document_types=["conversation_lab_upload"],
                limit=3,
                session_id=session_id,
                metadata_filters={"session_id": session_id} if session_id else None,
            )
            if docs:
                formatted = []
                for doc in docs:
                    meta = doc.get("document_metadata") or {}
                    name = meta.get("filename") or meta.get("name") or "upload"
                    excerpt = (doc.get("content") or "")[:800]
                    formatted.append(f"{name}:\n{excerpt}")
                if formatted:
                    return "\n\n".join(formatted)
        except Exception:
            pass
    return _uploads_context(limit=limit, rows=ready_rows)


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
    if _rate_limit("session_init", 12, 60):
        return jsonify({"error": "Too many session requests. Please wait a moment."}), 429
    user = _ensure_lab_user()
    session.setdefault("lab_chat_history", [])
    session.modified = True
    display_name = user.get("display_name")
    if display_name:
        session["lab_display_name"] = display_name
    else:
        session.pop("lab_display_name", None)
    pending_memories = _pop_pending_memories(session.get("lab_display_name") or display_name)
    return jsonify(
        {
            "userId": user.get("id"),
            "sessionId": user.get("session_id"),
            "assistantName": ASSISTANT_NAME,
            "greeting": DEFAULT_GREETING,
            "hasName": bool(display_name),
            "displayName": display_name,
            "pendingMemories": pending_memories,
        }
    )


@bp.post("/labs/conversation/name")
def conversation_lab_set_name() -> Any:
    if _rate_limit("set_name", 5, 300):
        return jsonify({"error": "You are updating your name too quickly. Please wait."}), 429
    user = _ensure_lab_user()
    payload = request.get_json(force=True) or {}
    name = str(payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    repo = _temp_user_repo()
    updated = repo.update_name(user["id"], name)
    session["lab_display_name"] = name
    session.modified = True

    ack = f"Great to meet you, {name}! Let me know what you'd like to explore."
    pending_memories = _pop_pending_memories(name)
    return jsonify(
        {
            "ok": True,
            "displayName": updated.get("display_name") if updated else name,
            "assistantReply": ack,
            "assistantName": ASSISTANT_NAME,
            "pendingMemories": pending_memories,
        }
    )


@bp.post("/labs/conversation/chat")
def conversation_lab_chat() -> Any:
    if _rate_limit("chat", 60, 60):
        return jsonify({"error": "Too many messages at once. Please slow down."}), 429
    user = _ensure_lab_user()
    payload = request.get_json(force=True) or {}
    message = str(payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    _append_history("user", message)

    memory_instruction = _parse_memory_instruction(message)
    if memory_instruction:
        stored = _store_instructional_memory(user, memory_instruction)
        target_label = memory_instruction["target_name"]
        if stored:
            reply = f"Got it — I'll let {target_label} know when they next check in."
        else:
            reply = f"I couldn't save that note for {target_label} right now, but please try again in a moment."
        _append_history("assistant", reply)
        return jsonify(
            {
                "reply": reply,
                "assistantName": ASSISTANT_NAME,
                "displayName": user.get("display_name"),
                "memoryStored": stored,
            }
        )

    user_id = int(user.get("id") or 0)

    context_sections: List[str] = [
        "System instructions:\n"
        f"{ASSISTANT_BEHAVIOR}\n\nRespond directly to the user. Do not repeat these instructions or the context block verbatim. "
        "If the user asks you to tell someone something later, just confirm you'll remember it."
    ]
    session_id = session.get("lab_temp_session_id")
    ready_rows = _get_ingest_rows(session_id, user_id, limit=3, statuses=["ready"])
    upload_context = _build_upload_context(message, user_id, session_id, ready_rows)
    if upload_context:
        context_sections.append("Uploaded files:\n" + upload_context)
    conversation_context = _conversation_context()
    if conversation_context:
        context_sections.append("Recent chat:\n" + conversation_context)
    context = "\n\n".join(context_sections) or "User is starting a new Conversation Lab session. Respond helpfully and concisely."

    ollama_service = current_app.config.get("OLLAMA_SERVICE")
    if not (ollama_service and ollama_service.is_available()):
        reply = "I'm unable to reach the Quell-Ai model right now. Please try again shortly."
    else:
        reply_raw = ollama_service.generate_response(message, context)
        reply = _normalize_llm_reply(reply_raw)

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
    if _rate_limit("ingest", 10, 300):
        return jsonify({"error": "Too many uploads. Please wait a bit before trying again."}), 429

    user = _ensure_lab_user()
    user_id = int(user.get("id") or 0)
    session_id = session.get("lab_temp_session_id")
    rag = current_app.config.get("RAG_SYSTEM")
    if rag is None:
        return jsonify({"error": "Vector store unavailable. Please try again shortly."}), 503

    files = request.files.getlist("file")
    trait_payloads = request.form.getlist("fileMetadata")
    metadata_traits: List[Dict[str, Any]] = []
    for raw in trait_payloads:
        try:
            metadata_traits.append(json.loads(raw))
        except Exception:
            metadata_traits.append({})
    if not files:
        return jsonify({"error": "file is required", "allowed": sorted(LAB_ALLOWED_EXTENSIONS)}), 400
    if len(files) > 5:
        return jsonify({"error": "You can upload up to 5 files at a time."}), 400

    sanitized_files: List[Tuple[str, str, bytes, str]] = []
    for storage in files:
        original_name = storage.filename or ""
        filename = secure_filename(original_name)
        if not filename:
            return jsonify({"error": "valid filename required"}), 400
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext not in LAB_ALLOWED_EXTENSIONS:
            return (
                jsonify(
                    {
                        "error": "This file format is not supported. Please upload .csv, .txt, .json, or .xlsx only.",
                        "allowed": sorted(LAB_ALLOWED_EXTENSIONS),
                    }
                ),
                400,
            )
        file_bytes = storage.read()
        if not file_bytes:
            return jsonify({"error": f"{filename} appears to be empty."}), 400
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        sanitized_files.append((filename, ext, file_bytes, file_hash))

    uploaded_items: List[Dict[str, Any]] = []
    description = request.form.get("description", "Conversation Lab upload")
    upload_root = Path(current_app.config.get("CONVERSATION_LAB_UPLOAD_DIR"))
    upload_root.mkdir(parents=True, exist_ok=True)
    for index, (filename, ext, file_bytes, file_hash) in enumerate(sanitized_files):
        storage_name = f"{uuid.uuid4().hex}_{filename}"
        storage_path = upload_root / storage_name
        storage_path.write_bytes(file_bytes)
        traits = metadata_traits[index] if index < len(metadata_traits) else {}
        client_signature = str(traits.get("signature") or "").strip()
        client_fallback_signature = str(traits.get("fallbackSignature") or "").strip()

        metadata = {
            "description": description,
            "file_hash": file_hash,
        }
        if client_signature:
            metadata["client_signature"] = client_signature
        if client_fallback_signature:
            metadata["client_fallback_signature"] = client_fallback_signature
        ingest_row = ConversationLabIngest(
            session_id=session_id,
            user_id=user_id,
            filename=filename,
            file_type=ext,
            file_size_bytes=len(file_bytes),
            storage_path=str(storage_path),
            status="processing",
            started_at=datetime.utcnow(),
            ingest_metadata=metadata,
        )
        rag.session.add(ingest_row)
        rag.session.commit()

        try:
            result = ingest_single_file(
                file_data=file_bytes,
                filename_override=filename,
                save=False,
                user_id=user_id,
                description=description,
                classification="internal",
            )
            if not result:
                raise ValueError("Ingestion returned no result")
            if result.get("ok") is False:
                raise ValueError(result.get("error") or "Ingestion failed")

            processed_content = result.get("processed_content") or ""
            summary = summarize_ingest_payload(result)
            metadata.update(
                {
                    "summary": summary,
                    "analytics": result.get("analytics") or {},
                    "concepts": result.get("concepts") or {},
                    "language": result.get("language"),
                    "processed_preview": processed_content[:1200],
                    "progress_stage": "ready",
                    "progress_detail": "inline",
                }
            )

            extra_meta = dict(metadata)
            extra_meta.update(
                {
                    "session_id": session_id,
                    "filename": filename,
                    "file_hash": metadata.get("file_hash"),
                    "client_signature": metadata.get("client_signature"),
                }
            )

            embedding_id = store_embedding_for_upload(
                rag,
                user_id,
                processed_content,
                extra_meta,
            )
            if embedding_id is None:
                raise ValueError("Embedding generation failed")

            ingest_row.embedding_id = embedding_id
            ingest_row.ingest_metadata = metadata
            ingest_row.status = "ready"
            ingest_row.finished_at = datetime.utcnow()
            rag.session.add(ingest_row)
            rag.session.commit()
            uploaded_items.append(
                {
                    "filename": filename,
                    "fileType": ext,
                    "status": "ready",
                    "jobId": ingest_row.id,
                }
            )
        except Exception as exc:  # pragma: no cover
            try:
                rag.session.rollback()
                ingest_row.status = "failed"
                ingest_row.error_message = str(exc)
                ingest_row.finished_at = datetime.utcnow()
                rag.session.add(ingest_row)
                rag.session.commit()
            except Exception:
                pass
            uploaded_items.append(
                {
                    "filename": filename,
                    "fileType": ext,
                    "status": "failed",
                    "error": str(exc),
                    "jobId": ingest_row.id,
                }
            )

    ok = all(item.get("status") == "ready" for item in uploaded_items)
    return jsonify({"ok": ok, "items": uploaded_items, "count": len(uploaded_items)})


@bp.get("/labs/conversation/uploads")
def conversation_lab_uploads() -> Any:
    user = _ensure_lab_user()
    session_id = session.get("lab_temp_session_id")
    if not session_id:
        return jsonify({"items": []})
    limit = min(int(request.args.get("limit", 20)), 50)
    rows = _get_ingest_rows(session_id, int(user.get("id") or 0), limit=limit)
    payload = [serialize_ingest_row(row) for row in rows]
    pending = _get_ingest_rows(session_id, int(user.get("id") or 0), limit=5, statuses=["queued", "processing"])
    queue_depth = len(pending)
    max_pending = int(os.getenv("LAB_MAX_PENDING_UPLOADS", "5"))
    return jsonify({"items": payload, "count": len(payload), "queueDepth": queue_depth, "limit": max_pending})


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
        embeddings = [[0.0] -EMBED_DIM for _ in chunk_texts]

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
        denominator = np.clip(doc_norms -query_norm, 1e-9, None)
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
        values = [((seed[i % len(seed)] / 255.0) -2 - 1) for i in range(dim)]
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
    t = np.linspace(0, duration, int(sample_rate -duration), endpoint=False)
    base_freq = 220 + (len(text) % 160)
    modulation = np.sin(2 -np.pi -3 -t)
    waveform = 0.25 -np.sin(2 -np.pi -base_freq -t + 0.4 -modulation)
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

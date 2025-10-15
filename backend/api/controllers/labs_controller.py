import base64
import hashlib
import math
import re
import uuid
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request

from api.services.labs_pipeline import DEFAULT_EMBED_DIM, LanguagePipelineClient

bp = Blueprint("labs", __name__)

TOKEN_LIMIT = 500
CHAR_FALLBACK = 1200
CHAR_OVERLAP = 200
PIPELINE_CLIENT = LanguagePipelineClient.from_env()
EMBED_DIM = PIPELINE_CLIENT.config.embed_dim or DEFAULT_EMBED_DIM


@dataclass
class Chunk:
    identifier: uuid.UUID
    order: int
    text: str


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


def _fallback_embed_many(texts: List[str], dim: int) -> List[List[float]]:
    embeddings: List[List[float]] = []
    for text in texts:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        values = [((seed[i % len(seed)] / 255.0) * 2 - 1) for i in range(dim)]
        embeddings.append([round(val, 6) for val in values])
    return embeddings


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

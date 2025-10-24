from __future__ import annotations

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """Detect language code of given text.

    Tries `langdetect` if available; falls back to simple heuristics.
    Returns ISO-like lowercase language code (e.g., 'en', 'es', 'fr').
    """
    try:
        if not text or not text.strip():
            return "en"
        try:
            # Optional dependency
            from langdetect import detect  # type: ignore

            return detect(text) or "en"
        except Exception:
            pass

        # Heuristic: assume English if mostly ASCII and common English words present
        ascii_ratio = sum(1 for ch in text if ord(ch) < 128) / max(1, len(text))
        en_cues = 0
        for token in (" the ", " and ", " is ", " are ", " of "):
            if token in text.lower():
                en_cues += 1
        if ascii_ratio > 0.95 and en_cues >= 1:
            return "en"
        # Unknown fallback
        return "unknown"
    except Exception as exc:
        logger.warning(f"Language detection failed: {exc}")
        return "unknown"


def translate_to_english(text: str, ollama_service) -> Tuple[str, Optional[str]]:
    """Translate non-English text to English using the Ollama LLM if available.

    Returns (translated_text, model_id). If translation not performed, returns original text and None.
    """
    try:
        if not text or not text.strip():
            return text, None

        if not ollama_service or not getattr(ollama_service, "is_available", lambda: False)():
            return text, None

        model_info = ollama_service.get_model_info() if hasattr(ollama_service, "get_model_info") else {}
        model_id = str(model_info.get("model_path", ""))

        # Build a strict translation prompt
        query = (
            "Translate the provided content into English. "
            "Output only the translation without commentary. Preserve numeric values and table-like structure when possible."
        )
        translated = ollama_service.generate_response(query, text)  # type: ignore[attr-defined]
        if not translated or not translated.strip():
            return text, None
        return translated.strip(), model_id
    except Exception as exc:
        logger.warning(f"Translation failed: {exc}")
        return text, None


import os
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Dict

import requests

DEFAULT_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_TRANSLATE_MODEL = "gpt-4o-mini"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_EMBED_DIM = 1536


@dataclass
class PipelineConfig:
    provider: str
    api_key: Optional[str]
    chat_model: str
    translate_model: str
    embed_model: str
    embed_dim: int
    api_base: str = "https://api.openai.com/v1"


class LanguagePipelineClient:
    """Thin wrapper that can call real providers (OpenAI first) with graceful fallbacks."""

    def __init__(self, config: PipelineConfig):
        self.config = config

    @classmethod
    def from_env(cls) -> "LanguagePipelineClient":
        provider = os.getenv("LABS_PIPELINE_PROVIDER", "fallback").lower()
        api_key = os.getenv("OPENAI_API_KEY")
        chat_model = os.getenv("LABS_OPENAI_MODEL", DEFAULT_CHAT_MODEL)
        translate_model = os.getenv("LABS_OPENAI_TRANSLATE_MODEL", chat_model or DEFAULT_TRANSLATE_MODEL)
        embed_model = os.getenv("LABS_OPENAI_EMBED_MODEL", DEFAULT_EMBED_MODEL)
        embed_dim = int(os.getenv("LABS_OPENAI_EMBED_DIM", DEFAULT_EMBED_DIM))
        api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
        config = PipelineConfig(
            provider=provider,
            api_key=api_key,
            chat_model=chat_model,
            translate_model=translate_model,
            embed_model=embed_model,
            embed_dim=embed_dim,
            api_base=api_base,
        )
        return cls(config)

    # ---- public API -----------------------------------------------------

    def detect_language(self, text: str) -> Optional[str]:
        if self._can_use_openai:
            try:
                prompt = (
                    "You are a language detection helper. "
                    "Return the ISO 639-1 language code (two lowercase letters) of the user's message. "
                    "If uncertain, respond with 'und'."
                )
                response = self._chat(prompt, text, model=self.config.chat_model, temperature=0.0)
                candidate = response.strip().lower()
                if re.fullmatch(r"[a-z]{2}", candidate):
                    return candidate
            except Exception:  # pragma: no cover - external API
                pass
        return None

    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        if source_lang == target_lang:
            return text
        if self._can_use_openai:
            try:
                prompt = (
                    f"Translate the following text from {source_lang} to {target_lang}. "
                    "Return only the translation, preserving numbers and key qualifiers."
                )
                result = self._chat(prompt, text, model=self.config.translate_model, temperature=0.0)
                return result.strip()
            except Exception:  # pragma: no cover - external API
                pass
        return None

    def summarize_chunk(self, text: str) -> Optional[str]:
        if self._can_use_openai:
            try:
                prompt = (
                    "Summarize the text into at most three bullet points. "
                    "Each bullet must preserve numbers, qualifiers, and negations."
                )
                content = self._chat(prompt, text, model=self.config.chat_model, temperature=0.1)
                lines = [line.strip(" -") for line in content.splitlines() if line.strip()]
                bullets = [f"- {line}" for line in lines[:3]]
                if bullets:
                    return "\n".join(bullets)
            except Exception:  # pragma: no cover - external API
                pass
        return None

    def reduce_summaries(self, summaries: Iterable[str]) -> Optional[str]:
        joined = "\n".join(summaries)
        if self._can_use_openai and joined.strip():
            try:
                prompt = (
                    "You receive bullet point summaries from multiple chunks. "
                    "Combine them into one concise short form (max 4 clauses) without inventing facts."
                )
                response = self._chat(prompt, joined, model=self.config.chat_model, temperature=0.0)
                final = response.replace("\n", " ").strip()
                return final if final else None
            except Exception:  # pragma: no cover - external API
                pass
        return None

    def embed_many(self, texts: List[str]) -> Optional[List[List[float]]]:
        if self._can_use_openai and texts:
            try:
                payload = {
                    "model": self.config.embed_model,
                    "input": texts,
                }
                response = requests.post(
                    f"{self.config.api_base}/embeddings",
                    headers=self._headers,
                    json=payload,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                embeddings = [entry["embedding"] for entry in data["data"]]
                return embeddings
            except Exception:  # pragma: no cover - external API
                pass
        return None

    # ---- internal -------------------------------------------------------

    @property
    def can_use_openai(self) -> bool:
        return self._can_use_openai

    @property
    def _can_use_openai(self) -> bool:
        return self.config.provider == "openai" and bool(self.config.api_key)

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def _chat(self, system_prompt: str, user_text: str, model: str, temperature: float) -> str:
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        }
        response = requests.post(
            f"{self.config.api_base}/chat/completions",
            headers=self._headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def chat_conversation(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 800,
    ) -> Optional[str]:
        if not messages:
            return None
        if not self._can_use_openai:
            return None
        try:
            payload = {
                "model": model or self.config.chat_model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            response = requests.post(
                f"{self.config.api_base}/chat/completions",
                headers=self._headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception:  # pragma: no cover - external API
            return None

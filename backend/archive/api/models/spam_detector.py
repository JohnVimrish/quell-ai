from __future__ import annotations
 
import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import phonenumbers
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from api.db.vector_store import SpamPattern
from api.utils.config import Config

logger = logging.getLogger(__name__)

DEFAULT_CLASSIFIER_MODEL = "gpt-4o-mini"
OPENAI_TIMEOUT = 20


class AdvancedSpamDetector:
    """Spam detection that leans on OpenAI with heuristic fallbacks."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
        engine = create_engine(self.config.database_url, future=True)
        SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        self.engine = engine
        self.session: Session = SessionFactory()

        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
        self.classifier_model = (
            os.getenv("OPENAI_SPAM_MODEL")
            or os.getenv("OPENAI_CHAT_MODEL")
            or os.getenv("LABS_OPENAI_MODEL")
            or DEFAULT_CLASSIFIER_MODEL
        )
        self._api_warning_emitted = False

        self.spam_keywords = [
            "congratulations",
            "winner",
            "free",
            "urgent",
            "limited time",
            "act now",
            "click here",
            "call now",
            "guaranteed",
            "risk-free",
            "no obligation",
            "cash",
            "money",
            "earn",
            "income",
            "investment",
            "loan",
            "credit",
            "debt",
            "refinance",
            "mortgage",
            "insurance",
            "pharmacy",
            "medication",
            "pills",
            "viagra",
            "cialis",
        ]
        self.urgency_patterns = [
            r"act\s+now",
            r"limited\s+time",
            r"expires\s+today",
            r"urgent\s+response",
            r"immediate\s+action",
            r"don't\s+wait",
        ]
        self.phone_patterns = [
            r"\b1-?800-?\d{3}-?\d{4}\b",
            r"\b\d{3}-?\d{3}-?\d{4}\b",
            r"\(\d{3}\)\s?\d{3}-?\d{4}",
        ]

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def analyze_text_spam(self, text: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """Classify text using heuristics augmented by OpenAI."""
        try:
            heuristics = self._heuristic_text_scores(text)
            phone_analysis = self._analyze_phone_number(phone_number) if phone_number else None
            ai_result = self._classify_with_openai(
                channel="sms",
                text=text,
                extra={"phone_number": phone_number} if phone_number else None,
            )

            weighted_sum = 0.0
            weight_total = 0.0

            def add_component(score: Optional[float], weight: float) -> None:
                nonlocal weighted_sum, weight_total
                if score is None:
                    return
                weighted_sum += score * weight
                weight_total += weight

            add_component(heuristics["keyword_score"], 0.2)
            add_component(heuristics["urgency_score"], 0.1)
            add_component(heuristics["structure_score"], 0.1)
            if phone_analysis:
                add_component(phone_analysis["spam_score"], 0.15)
            if ai_result:
                add_component(ai_result["probability"], 0.6)

            final_score = weighted_sum / weight_total if weight_total else 0.0
            final_score = max(0.0, min(final_score, 1.0))
            is_spam = final_score >= 0.6

            indicators: List[str] = list(heuristics["indicators"])
            if phone_analysis:
                indicators.extend(phone_analysis["indicators"])
            if ai_result and ai_result.get("reason"):
                indicators.append(ai_result["reason"])

            details: Dict[str, Any] = {
                "keyword_score": heuristics["keyword_score"],
                "urgency_score": heuristics["urgency_score"],
                "structure_score": heuristics["structure_score"],
            }
            if phone_analysis:
                details["phone_score"] = phone_analysis["spam_score"]
            if ai_result:
                details["openai_probability"] = ai_result["probability"]
                details["openai_label"] = ai_result["label"]

            if is_spam:
                self._store_spam_pattern(text, "text", final_score)

            return {
                "is_spam": is_spam,
                "spam_score": final_score,
                "confidence": final_score,
                "indicators": self._unique(indicators),
                "analysis_details": details,
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing text spam: %s", exc)
            return {
                "is_spam": False,
                "spam_score": 0.0,
                "confidence": 0.0,
                "indicators": [],
                "error": str(exc),
            }

    def analyze_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess call metadata and optional transcript."""
        try:
            phone_number = call_data.get("from_number") or ""
            duration = int(call_data.get("duration_seconds") or 0)
            time_of_day = call_data.get("time_of_day")
            transcript = call_data.get("transcript") or ""

            phone_analysis = self._analyze_phone_number(phone_number)
            duration_score = self._call_duration_score(duration)
            time_score = self._call_time_score(time_of_day)
            transcript_result = (
                self.analyze_text_spam(transcript, phone_number) if transcript else None
            )

            ai_result: Optional[Dict[str, Any]] = None
            if not transcript and call_data and self._api_available:
                summary = (
                    f"Incoming call from {phone_number or 'unknown'} to {call_data.get('to_number', 'unknown')}."
                    f" Duration {duration} seconds. Hour of day: {time_of_day!s}."
                )
                ai_result = self._classify_with_openai(
                    channel="call",
                    text=summary,
                    extra={
                        "from_number": phone_number,
                        "to_number": call_data.get("to_number"),
                        "duration_seconds": duration,
                        "time_of_day": time_of_day,
                    },
                )

            weighted_sum = 0.0
            weight_total = 0.0

            def add_component(score: Optional[float], weight: float) -> None:
                nonlocal weighted_sum, weight_total
                if score is None:
                    return
                weighted_sum += score * weight
                weight_total += weight

            add_component(phone_analysis["spam_score"], 0.25)
            add_component(duration_score, 0.15)
            add_component(time_score, 0.1)
            if transcript_result:
                add_component(transcript_result["spam_score"], 0.45)
            if ai_result:
                add_component(ai_result["probability"], 0.35)

            final_score = weighted_sum / weight_total if weight_total else 0.0
            final_score = max(0.0, min(final_score, 1.0))
            is_spam = final_score >= 0.6

            indicators: List[str] = []
            indicators.extend(phone_analysis["indicators"])
            if duration_score > 0.4:
                indicators.append("Suspiciously short duration")
            if time_score > 0.4:
                indicators.append("Call occurred at an unusual time")
            if transcript_result:
                indicators.extend(transcript_result["indicators"])
            if ai_result and ai_result.get("reason"):
                indicators.append(ai_result["reason"])

            details: Dict[str, Any] = {
                "phone_score": phone_analysis["spam_score"],
                "duration_score": duration_score,
                "time_score": time_score,
                "transcript_score": transcript_result["spam_score"] if transcript_result else 0.0,
            }
            if ai_result:
                details["openai_probability"] = ai_result["probability"]
                details["openai_label"] = ai_result["label"]

            if is_spam:
                preview = transcript[:120] if transcript else f"Call from {phone_number}"
                self._store_spam_pattern(preview, "call", final_score)

            return {
                "is_spam": is_spam,
                "spam_score": final_score,
                "confidence": final_score,
                "indicators": self._unique(indicators),
                "analysis_details": details,
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing call spam: %s", exc)
            return {
                "is_spam": False,
                "spam_score": 0.0,
                "confidence": 0.0,
                "indicators": [],
                "error": str(exc),
            }

    def analyze_call_spam(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility alias for legacy callers."""
        return self.analyze_call(call_data)

    def get_spam_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Summarize spam activity for dashboards."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            call_stats = self.session.execute(
                text(
                    """
                    SELECT COUNT(*) AS total_calls,
                           SUM(CASE WHEN spam_score >= 0.6 THEN 1 ELSE 0 END) AS spam_calls
                    FROM calls
                    WHERE started_at >= :cutoff
                    """
                ),
                {"cutoff": cutoff},
            ).first()

            text_stats = self.session.execute(
                text(
                    """
                    SELECT COUNT(*) AS total_texts,
                           SUM(CASE WHEN spam_flag = true THEN 1 ELSE 0 END) AS spam_texts
                    FROM texts
                    WHERE ts >= :cutoff
                    """
                ),
                {"cutoff": cutoff},
            ).first()

            total_calls = call_stats.total_calls if call_stats else 0
            spam_calls = call_stats.spam_calls if call_stats else 0
            total_texts = text_stats.total_texts if text_stats else 0
            spam_texts = text_stats.spam_texts if text_stats else 0

            return {
                "period_days": days,
                "calls": {
                    "total": total_calls,
                    "spam": spam_calls,
                    "spam_rate": (spam_calls / total_calls) if total_calls else 0.0,
                },
                "texts": {
                    "total": total_texts,
                    "spam": spam_texts,
                    "spam_rate": (spam_texts / total_texts) if total_texts else 0.0,
                },
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("Error gathering spam statistics: %s", exc)
            return {"error": str(exc)}

    def cleanup(self) -> None:
        """Release database resources."""
        try:
            if hasattr(self, "session") and self.session:
                self.session.close()
        except Exception as exc:  # noqa: BLE001
            logger.error("Error closing spam detector session: %s", exc)

        try:
            if hasattr(self, "engine") and self.engine:
                self.engine.dispose()
        except Exception as exc:  # noqa: BLE001
            logger.error("Error disposing spam detector engine: %s", exc)

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    @property
    def _api_available(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _log_missing_key_once(self) -> None:
        if not self._api_warning_emitted:
            logger.warning("OPENAI_API_KEY is not configured; spam detection will rely on heuristics only.")
            self._api_warning_emitted = True

    def _classify_with_openai(
        self,
        channel: str,
        text: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self._api_available:
            self._log_missing_key_once()
            return None

        payload = {
            "channel": channel,
            "text": text,
            "metadata": extra or {},
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "Classify whether the message is spam. "
                    "Respond with JSON containing keys: "
                    "'label' (spam or ham), 'spam_probability' (float 0-1), "
                    "and 'reason' (short string)."
                ),
            },
            {"role": "user", "content": json.dumps(payload)},
        ]

        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self._headers(),
                json={
                    "model": self.classifier_model,
                    "temperature": 0.0,
                    "messages": messages,
                    "max_tokens": 200,
                },
                timeout=OPENAI_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = self._safe_json(content)
            if not parsed:
                return None

            probability = parsed.get("spam_probability")
            try:
                probability = float(probability)
            except (TypeError, ValueError):
                probability = None

            label = str(parsed.get("label", "")).strip().lower()
            if label not in {"spam", "ham"}:
                label = "unknown"

            if probability is None:
                probability = 0.5
            probability = max(0.0, min(1.0, probability))

            return {
                "probability": probability,
                "label": label,
                "reason": str(parsed.get("reason", "")).strip(),
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenAI spam classification failed: %s", exc)
            return None

    def _heuristic_text_scores(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        indicators: List[str] = []

        keywords = [kw for kw in self.spam_keywords if kw in text_lower]
        keyword_score = min(len(keywords) / 4, 1.0)
        if keywords:
            preview = ", ".join(sorted(set(keywords))[:5])
            indicators.append(f"Common spam keywords detected: {preview}")

        urgency_matches = [pat for pat in self.urgency_patterns if re.search(pat, text_lower)]
        urgency_score = min(len(urgency_matches) / 3, 1.0)
        if urgency_matches:
            indicators.append("Urgent language detected")

        alpha_chars = [ch for ch in text if ch.isalpha()]
        uppercase_ratio = (
            sum(1 for ch in alpha_chars if ch.isupper()) / len(alpha_chars) if alpha_chars else 0.0
        )
        exclamation_ratio = min(text.count("!") / max(len(text), 1) * 5, 1.0)
        structure_score = min(uppercase_ratio * 0.5 + exclamation_ratio, 1.0)
        if structure_score > 0.4:
            indicators.append("Aggressive formatting (caps or punctuation)")

        return {
            "keyword_score": keyword_score,
            "urgency_score": urgency_score,
            "structure_score": structure_score,
            "indicators": indicators,
        }

    def _analyze_phone_number(self, phone_number: Optional[str]) -> Dict[str, Any]:
        if not phone_number:
            return {"spam_score": 0.0, "is_suspicious": False, "indicators": []}

        spam_score = 0.0
        indicators: List[str] = []

        try:
            parsed = phonenumbers.parse(phone_number, "US")
            is_valid = phonenumbers.is_valid_number(parsed)
            if not is_valid:
                spam_score += 0.3
                indicators.append("Invalid phone number format")
        except phonenumbers.NumberParseException:
            spam_score += 0.4
            indicators.append("Unparseable phone number")

        digits_only = re.sub(r"\D", "", phone_number)
        if digits_only.startswith(("800", "888", "877", "866", "855", "844", "833")):
            spam_score += 0.2
            indicators.append("Toll-free origin often used for spam")

        if re.search(r"(.)\1{2,}", digits_only):
            spam_score += 0.2
            indicators.append("Repeated digit pattern detected")

        for pattern in self.phone_patterns:
            if re.search(pattern, phone_number):
                spam_score += 0.1
                break

        return {
            "spam_score": min(spam_score, 1.0),
            "is_suspicious": spam_score > 0.5,
            "indicators": indicators,
        }

    def _call_duration_score(self, duration: int) -> float:
        if duration <= 5:
            return 0.8
        if duration <= 15:
            return 0.5
        if duration <= 30:
            return 0.3
        if duration <= 90:
            return 0.1
        return 0.0

    def _call_time_score(self, hour: Optional[int]) -> float:
        if hour is None:
            return 0.0
        if hour < 6 or hour >= 22:
            return 0.7
        if hour < 9 or hour >= 20:
            return 0.4
        if hour < 12 or hour >= 18:
            return 0.2
        return 0.05

    def _store_spam_pattern(self, content: str, pattern_type: str, confidence: float) -> None:
        try:
            pattern = SpamPattern(
                pattern_type=pattern_type,
                pattern_data=content[:500],
                confidence_score=float(confidence),
            )
            self.session.add(pattern)
            self.session.commit()
        except Exception as exc:  # noqa: BLE001
            self.session.rollback()
            logger.debug("Failed to store spam pattern: %s", exc)

    def _safe_json(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"{.*}", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    return None
        return None

    def _unique(self, items: List[str]) -> List[str]:
        seen = set()
        unique_items = []
        for item in items:
            normalized = item.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_items.append(normalized)
        return unique_items

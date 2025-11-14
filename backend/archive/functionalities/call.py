from __future__ import annotations

from typing import Any, Dict

from functionalities.communication_session import (
    CallSession,
    SessionParticipant,
    SessionTranscript,
)


class Call(CallSession):
    """Backwards compatible alias for phone call sessions."""

    __mapper_args__ = {"polymorphic_identity": "call"}

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        metadata = self.session_metadata or {}
        data.update(
            {
                "recording_url": self.recording_url,
                "caller_number": metadata.get("caller_number")
                or metadata.get("from_number"),
                "callee_number": metadata.get("callee_number")
                or metadata.get("to_number"),
                "caller_name": self.counterpart_name,
                "from_number": metadata.get("from_number")
                or metadata.get("caller_number"),
                "to_number": metadata.get("to_number")
                or metadata.get("callee_number"),
                "call_type": self.direction,
                "is_spam": metadata.get("is_spam"),
                "spam_score": metadata.get("spam_score"),
                "notes": metadata.get("notes"),
                "tags": metadata.get("tags") or [],
            }
        )
        return data


CallParticipant = SessionParticipant
CallTranscript = SessionTranscript

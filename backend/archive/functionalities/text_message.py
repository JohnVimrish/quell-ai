from __future__ import annotations

from typing import Any, Dict

from functionalities.communication_session import (
    ChatSession,
    SessionMessage,
)


class TextConversation(ChatSession):
    """Backwards compatible alias for chat conversations."""

    __mapper_args__ = {"polymorphic_identity": "chat"}

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "channel": self.channel,
                "counterpart_identifier": self.counterpart_identifier,
                "counterpart_name": self.counterpart_name,
            }
        )
        return data


class TextMessage(SessionMessage):
    """Alias to keep legacy imports functioning."""

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "direction": self.direction,
                "message_text": self.content,
                "message_type": self.content_type,
                "metadata": self.message_metadata or {},
            }
        )
        return data


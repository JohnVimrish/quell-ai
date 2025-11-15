"""
Lightweight export surface for ORM models used around the API.
Some legacy models are archived; imports below are tolerant to missing modules.
"""

try:
    from functionalities.contacts import Contact, ContactNote as ImportantContact  # type: ignore
except Exception:  # archived or unavailable
    Contact = None  # type: ignore
    ImportantContact = None  # type: ignore

try:
    from functionalities.user import User  # type: ignore
except Exception:
    User = None  # type: ignore

try:
    from functionalities.call import Call, CallTranscript  # type: ignore
except Exception:
    Call = None  # type: ignore
    CallTranscript = None  # type: ignore

try:
    from functionalities.text_message import TextMessage, TextConversation  # type: ignore
except Exception:
    TextMessage = None  # type: ignore
    TextConversation = None  # type: ignore

try:
    from functionalities.ai_instruction import AIInstruction  # type: ignore
except Exception:
    AIInstruction = None  # type: ignore

try:
    from functionalities.voice_model import VoiceModel  # type: ignore
except Exception:
    VoiceModel = None  # type: ignore

try:
    from functionalities.analytics import CallAnalytics, WeeklyReport  # type: ignore
except Exception:
    CallAnalytics = None  # type: ignore
    WeeklyReport = None  # type: ignore

# Expose only the names that resolved successfully
_exports = {
    'User': User,
    'VoiceModel': VoiceModel
}

__all__ = [name for name, val in _exports.items() if val is not None]

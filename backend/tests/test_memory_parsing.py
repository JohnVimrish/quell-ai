from __future__ import annotations

from api.controllers import labs_controller


def test_parse_memory_requires_prefix() -> None:
    """Without the savememory- prefix, messages should not be treated as memories."""
    assert labs_controller._parse_memory_instruction("remember Alice to call") is None
    assert labs_controller._parse_memory_instruction("let Bob know about the meeting") is None


def test_parse_memory_with_prefix() -> None:
    payload = labs_controller._parse_memory_instruction("savememory- remind Carla to review the deck")
    assert payload is not None
    assert payload["target_name"] == "Carla"
    assert "review the deck" in payload["memory_text"]

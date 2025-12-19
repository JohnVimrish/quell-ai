from __future__ import annotations

from typing import Callable

from api.models import rag_system


def _mock_sha1(digest_bytes: bytes) -> Callable[[bytes], object]:
    class _DummyHash:
        def __init__(self, blob: bytes) -> None:
            self._blob = blob

        def digest(self) -> bytes:
            return self._blob

    def _factory(_data: bytes) -> _DummyHash:
        return _DummyHash(digest_bytes)

    return _factory


def test_derive_file_id_is_clamped_to_signed_int(monkeypatch) -> None:
    """Ensure derived IDs never exceed the signed INT range used in Postgres."""
    dummy = object.__new__(rag_system.RAGSystem)
    # Force the high bit so the unclamped value would overflow INT32.
    monkeypatch.setattr(rag_system.hashlib, "sha1", _mock_sha1(b"\xFF\xFF\xFF\xFF" + b"\x00" * 16))
    result = rag_system.RAGSystem._derive_file_id(dummy, None, {"filename": "foo.txt"}, 99)
    assert 0 < result <= 0x7FFFFFFF


def test_derive_file_id_never_returns_zero(monkeypatch) -> None:
    """When the digest results in zero, fall back to 1 to keep a positive ID."""
    dummy = object.__new__(rag_system.RAGSystem)
    monkeypatch.setattr(rag_system.hashlib, "sha1", _mock_sha1(b"\x00" * 20))
    result = rag_system.RAGSystem._derive_file_id(dummy, None, {"session_id": "abc"}, 99)
    assert result == 1

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from api.models.embedding_provider import EmbeddingTimeoutError
from scripts.ingest_file import ingest_single_file


@patch("scripts.ingest_file.get_embedding_backend")
@patch("scripts.ingest_file.OllamaService")
def test_ingest_returns_error_when_embedding_times_out(mock_service_cls, mock_backend_factory, tmp_path):
    """Ingestion should surface a friendly error if the embedding call hangs."""
    fake_file = tmp_path / "sample.txt"
    fake_file.write_text("Sample English content for timeout testing.", encoding="utf-8")

    service_instance = MagicMock()
    service_instance.is_available.return_value = True
    service_instance.get_model_info.return_value = {"model_name": "mock"}
    mock_service_cls.return_value = service_instance

    backend = MagicMock()
    backend.label = "sentence_transformer:test"
    backend.embed.side_effect = EmbeddingTimeoutError("timeout")
    mock_backend_factory.return_value = backend

    result = ingest_single_file(
        file_path=Path(fake_file),
        save=False,
        user_id=1,
        description="test",
        classification="internal",
    )

    assert result["ok"] is False
    assert "timed out" in result["error"].lower()

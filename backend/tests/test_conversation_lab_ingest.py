from __future__ import annotations

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from api.app import create_app


@patch("api.controllers.labs_controller.store_embedding_for_upload", return_value=99)
@patch("api.controllers.labs_controller.ingest_multiple_files")
def test_conversation_lab_ingest_flow(ingest_mock, store_mock):
    """Simulate the front-end upload flow via the Flask test client."""

    ingest_mock.return_value = [
        {
            "ok": True,
            "processed_content": "CSV file with columns: Name, Age",
            "analytics": {"row_count": 2},
            "concepts": {"summary": "Names and ages"},
            "language": "en",
            "vector": [0.1, 0.2],
            "document": {"id": 123, "name": "sample.csv"},
            "saved": True,
        }
    ]

    app = create_app()
    app.config["CONVERSATION_LAB_DOC_USER_ID"] = 555
    client = app.test_client()

    # Initialize Conversation Lab session (creates temp user + session cookie)
    session_resp = client.post("/api/labs/conversation/session")
    assert session_resp.status_code == 200

    data = {
        "description": "Pytest upload",
        "file": (BytesIO(b"Name,Age\nAlice,30"), "sample.csv"),
    }

    resp = client.post(
        "/api/labs/conversation/ingest",
        data=data,
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["items"], "expected upload metadata"
    assert payload["items"][0]["status"] == "ready"
    ingest_mock.assert_called_once()
    store_mock.assert_called_once()


class DummySession:
    def add(self, _obj):
        return None

    def commit(self):
        return None

    def rollback(self):
        return None


class DummyRAG:
    def __init__(self):
        self.session = DummySession()


@patch("api.controllers.labs_controller.store_embedding_for_upload", return_value=21)
@patch("api.controllers.labs_controller.ingest_multiple_files")
def test_conversation_lab_ingest_with_real_file(ingest_mock, store_mock):
    app = create_app()
    app.config["CONVERSATION_LAB_DOC_USER_ID"] = 555
    app.config["RAG_SYSTEM"] = DummyRAG()
    client = app.test_client()

    ingest_mock.return_value = [
        {
            "ok": True,
            "processed_content": "Pizza sales data",
            "analytics": {"row_count": 10},
            "concepts": {"summary": "pizza sales"},
            "language": "en",
            "vector": [0.01, 0.02],
            "document": {"id": 321, "name": "test.csv"},
            "saved": True,
        }
    ]

    resp = client.post("/api/labs/conversation/session")
    assert resp.status_code == 200

    test_csv = Path("test.csv")
    assert test_csv.exists(), "test.csv must exist in project root for this test"

    with test_csv.open("rb") as handle:
        data = {
            "description": "Test via TSX sim",
            "file": (handle, test_csv.name),
        }
        ingest_resp = client.post(
            "/api/labs/conversation/ingest",
            data=data,
            content_type="multipart/form-data",
        )

    assert ingest_resp.status_code == 200
    payload = ingest_resp.get_json()
    assert payload["ok"] is True
    assert payload["items"], "expected at least one ingest record"
    assert payload["items"][0]["status"] == "ready"
    ingest_mock.assert_called_once()
    store_mock.assert_called_once()


@patch("api.controllers.labs_controller.store_embedding_for_upload", return_value=99)
@patch("api.controllers.labs_controller.ingest_multiple_files")
def test_conversation_lab_ingest_persists_documents(ingest_mock, store_mock):
    ingest_mock.return_value = [
        {
            "ok": True,
            "processed_content": "hello",
            "analytics": {},
            "concepts": {},
            "language": "en",
            "vector": [0.1],
            "document": {"id": 42, "name": "hello.txt"},
            "saved": True,
        }
    ]
    app = create_app()
    app.config["CONVERSATION_LAB_DOC_USER_ID"] = 777
    client = app.test_client()

    resp = client.post("/api/labs/conversation/session")
    assert resp.status_code == 200

    data = {
        "description": "Persist please",
        "file": (BytesIO(b"Hello world"), "hello.txt"),
    }
    resp = client.post(
        "/api/labs/conversation/ingest",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    ingest_mock.assert_called_once()
    args, kwargs = ingest_mock.call_args
    assert kwargs["save"] is True
    assert kwargs["user_id"] == 777


@patch("api.controllers.labs_controller.store_embedding_for_upload", return_value=77)
@patch("api.controllers.labs_controller.ingest_multiple_files")
@patch("api.controllers.labs_controller.PIPELINE_CLIENT")
def test_conversation_lab_ingest_pizza_prompt(pipeline_mock, ingest_mock, store_mock):
    """Upload PizzaSales.csv and ensure the prompt is routed to the chat pipeline."""

    ingest_mock.return_value = [
        {
            "ok": True,
            "processed_content": "Pizza sales data",
            "analytics": {"row_count": 10},
            "concepts": {"summary": "pizza sales"},
            "language": "en",
            "vector": [0.01, 0.02],
            "document": {"id": 321, "name": "PizzaSales.csv"},
            "saved": True,
        }
    ]
    pipeline_mock.chat_conversation.return_value = "5 orders match that pizza."

    app = create_app()
    app.config["CONVERSATION_LAB_DOC_USER_ID"] = 555
    client = app.test_client()

    resp = client.post("/api/labs/conversation/session")
    assert resp.status_code == 200

    pizza_path = Path("PizzaSales.csv")
    assert pizza_path.exists(), "PizzaSales.csv must exist in project root for this test"

    with pizza_path.open("rb") as handle:
        data = {
            "description": "Pizza upload",
            "file": (handle, pizza_path.name),
        }
        ingest_resp = client.post(
            "/api/labs/conversation/ingest",
            data=data,
            content_type="multipart/form-data",
        )
    assert ingest_resp.status_code == 200

    chat_resp = client.post(
        "/api/labs/conversation/chat",
        json={"message": "how many records are present for pizza_name = 'The California Chicken Pizza'"},
    )
    assert chat_resp.status_code == 200
    payload = chat_resp.get_json()
    assert payload["reply"] == "5 orders match that pizza."
    pipeline_mock.chat_conversation.assert_called()
    store_mock.assert_called_once()

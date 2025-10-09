from api.app import create_app


def test_health_endpoint_returns_payload():
    app = create_app()
    client = app.test_client()

    response = client.get("/api/status/health")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["status"] in {"ok", "degraded"}
    assert "components" in payload
    assert "database" in payload["components"]
    assert "features" in payload
    assert set(payload["features"].keys()) >= {
        "spam_detection",
        "retrieval_augmented_generation",
        "voice_cloning",
    }

import json
from api.app import create_app

def test_healthz():
    app = create_app()
    client = app.test_client()
    r = client.get('/healthz')
    assert r.status_code == 200
    assert r.json.get('status') == 'ok'

def test_feed_active_empty(monkeypatch):
    app = create_app()
    client = app.test_client()

    class FakeRepo:
        def __init__(self, *_args, **_kwargs): pass
        def list_active(self, user_id:int): return []

    import api.controllers.feed_controller as fc
    fc.FeedRepository = FakeRepo

    r = client.get('/api/feed/active')
    assert r.status_code == 200
    assert r.json == []

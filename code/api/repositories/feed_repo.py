from dataclasses import dataclass
from datetime import datetime, timedelta
from api.repositories.base import BaseRepository

@dataclass
class FeedItem:
    id: int | None
    user_id: int
    title: str
    body: str
    tags: list[str]
    status: str
    created_at: datetime
    expires_at: datetime

class FeedRepository(BaseRepository):
    def create(self, user_id: int, title: str, body: str, tags: list[str]):
        now = datetime.utcnow()
        expires = now + timedelta(days=7)
        rows = self.execute("feed_create", [user_id, title, body, tags, "active", now, expires])
        return rows[0] if rows else None

    def list_active(self, user_id: int):
        return self.execute("feed_active_by_user", [user_id])

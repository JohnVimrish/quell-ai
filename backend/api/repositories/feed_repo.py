from dataclasses import dataclass
from datetime import datetime, timedelta
from api.repositories.base import BaseRepository
from typing import List, Dict

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
    """Repository for managing feed items in the database."""
    
    def __init__(self, database_url: str, queries_config: Dict):
        super().__init__(database_url)
        self.queries = queries_config
        self.model_class = FeedItem
    
    def create(self, user_id: int, title: str, body: str, tags: list[str]):
        now = datetime.utcnow()
        expires = now + timedelta(days=7)
        rows = self.execute("feed_create", [user_id, title, body, tags, "active", now, expires])
        return rows[0] if rows else None

    def list_active(self, user_id: int) -> List[Dict]:
            """Lists all active feed items for a user."""
            query = self.queries['feed']['list_active']
            params = [user_id]
            results = self.execute(query, params)
            return [self.model_class.from_db(row).to_dict() for row in results] if results else []


    def get_by_id(self, item_id: int) -> Dict | None:
        """Retrieves a feed item by its ID."""
        query = self.queries['feed']['get_by_id']
        params = [item_id]
        results = self.execute(query, params)
        return self.model_class.from_db(results[0]).to_dict() if results else None
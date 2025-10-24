from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy import text
from api.repositories.base import BaseRepository


class FeedRepository(BaseRepository):
    """Repository for managing feed items (SQLAlchemy Core + queries.json)."""

    def __init__(self, database_url: str, queries_config: Dict):
        super().__init__(database_url, queries_config)

    def create(self, user_id: int, title: str, body: str, tags: List[str]):
        now = datetime.utcnow()
        expires = now + timedelta(days=7)
        sql = self.queries['feed']['create']
        sql_conv, bind_map = self._prepare_sql(sql, [user_id, title, body, tags, 'active', now, expires])
        with self.engine.begin() as conn:
            result = conn.execute(text(sql_conv), bind_map)
            row = result.mappings().first()
            return dict(row) if row else None

    def list_active(self, user_id: int) -> List[Dict]:
        sql = self.queries['feed']['list_active']
        sql_conv, bind_map = self._prepare_sql(sql, [user_id])
        with self.engine.begin() as conn:
            result = conn.execute(text(sql_conv), bind_map)
            return [dict(r) for r in result.mappings().all()]

    def get_by_id(self, item_id: int) -> Dict | None:
        sql = self.queries['feed']['get_by_id']
        sql_conv, bind_map = self._prepare_sql(sql, [item_id])
        with self.engine.begin() as conn:
            result = conn.execute(text(sql_conv), bind_map)
            row = result.mappings().first()
            return dict(row) if row else None

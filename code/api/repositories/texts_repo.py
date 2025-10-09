
from typing import List, Dict, Optional
from api.repositories.base import BaseRepository
from functionalities.text_message import TextMessage

class TextsRepository(BaseRepository):
    """Repository for handling text messages."""

    def __init__(self, database_url: str, queries_config: Dict):
        super().__init__(database_url)
        self.queries = queries_config
        self.model_class = TextMessage

    def search_messages(self, user_id: int, query: str, page: int, limit: int, contact_id: Optional[int] = None) -> List[Dict]:
        """Search for messages by content."""
        search_query = self.queries['texts']['search_messages']
        offset = (page - 1) * limit
        like_query = f"%{query}%"
        params = [user_id, like_query, contact_id, contact_id, limit, offset]
        
        results = self.execute(search_query, params)
        return [self.model_class.from_db(row).to_dict() for row in results] if results else []

    def count_search_results(self, user_id: int, query: str, contact_id: Optional[int] = None) -> int:
        """Count the total number of search results."""
        count_query = self.queries['texts']['count_search_results']
        like_query = f"%{query}%"
        params = [user_id, like_query, contact_id, contact_id]
        
        result = self.execute(count_query, params)
        return result[0][0] if result else 0

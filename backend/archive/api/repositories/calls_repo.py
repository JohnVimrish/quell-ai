from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CallsRepository:
    """Archived placeholder for call operations. Returns safe defaults."""

    def __init__(self, database_url: str, _queries_config: Optional[Dict] = None):
        self.database_url = database_url
        logger.info("CallsRepository is archived/disabled")

    # Listing/counting
    def list_calls(self, filters: Dict, page: int, limit: int) -> List[Dict]:
        logger.debug("list_calls skipped (archived)")
        return []

    def count_calls(self, filters: Dict) -> int:
        logger.debug("count_calls skipped (archived)")
        return 0

    def get_call(self, call_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
        logger.debug("get_call skipped (archived)")
        return None

    def get_recent_calls(self, user_id: int, limit: int = 20, include_spam: bool = False) -> List[Dict]:
        logger.debug("get_recent_calls skipped (archived)")
        return []

    def get_calls_by_date_range(self, user_id: int, start_date, end_date) -> List[Dict]:
        logger.debug("get_calls_by_date_range skipped (archived)")
        return []

    # Mutations
    def create_call(self, call_data: Dict) -> Optional[int]:
        logger.debug("create_call skipped (archived)")
        return None

    def update_call(self, call_id: int, update_data: Dict) -> bool:
        logger.debug("update_call skipped (archived)")
        return False

    def delete_call(self, call_id: int, user_id: int) -> bool:
        logger.debug("delete_call skipped (archived)")
        return False

    def bulk_delete_calls(self, user_id: int, call_ids: List[int]) -> int:
        logger.debug("bulk_delete_calls skipped (archived)")
        return 0

    # Analytics & search
    def get_call_statistics(self, user_id: int, days: int = 30) -> Dict:
        logger.debug("get_call_statistics skipped (archived)")
        return {}

    def get_call_stats(self, user_id: int, start_date, end_date) -> Dict:
        logger.debug("get_call_stats skipped (archived)")
        return {}

    def search_calls(self, user_id: int, query: str, page: int, limit: int) -> List[Dict]:
        logger.debug("search_calls skipped (archived)")
        return []

    def count_search_results(self, user_id: int, query: str) -> int:
        logger.debug("count_search_results skipped (archived)")
        return 0

    # Legacy helpers
    def get_call_by_external_id(self, external_id: str) -> Optional[Dict]:
        logger.debug("get_call_by_external_id skipped (archived)")
        return None

    def mark_as_spam(self, call_id: int, user_id: int) -> bool:
        logger.debug("mark_as_spam skipped (archived)")
        return False

    def unmark_spam(self, call_id: int, user_id: int) -> bool:
        logger.debug("unmark_spam skipped (archived)")
        return False


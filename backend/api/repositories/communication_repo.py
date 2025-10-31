from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CommunicationRepository:
    """Archived placeholder for session/message store. Returns safe defaults."""

    def __init__(self, database_url: str, *_: object, **__: object) -> None:
        self.database_url = database_url
        logger.info("CommunicationRepository is archived/disabled")

    # Sessions
    def list_sessions(self, filters: Dict, page: int, limit: int) -> List[Dict]:
        logger.debug("list_sessions skipped (archived)")
        return []

    def count_sessions(self, filters: Dict) -> int:
        logger.debug("count_sessions skipped (archived)")
        return 0

    def get_session(self, session_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
        logger.debug("get_session skipped (archived)")
        return None

    def get_recent_sessions(self, user_id: int, session_type: str, limit: int) -> List[Dict]:
        logger.debug("get_recent_sessions skipped (archived)")
        return []

    def create_session(self, payload: Dict) -> Optional[int]:
        logger.debug("create_session skipped (archived)")
        return None

    def update_session(self, session_id: int, updates: Dict) -> bool:
        logger.debug("update_session skipped (archived)")
        return False

    def delete_session(self, session_id: int, user_id: int) -> bool:
        logger.debug("delete_session skipped (archived)")
        return False

    def bulk_delete_sessions(self, user_id: int, ids: List[int]) -> int:
        logger.debug("bulk_delete_sessions skipped (archived)")
        return 0

    def upsert_transcript(self, session_id: int, payload: Dict) -> bool:
        logger.debug("upsert_transcript skipped (archived)")
        return False

    # Search
    def search_sessions(self, user_id: int, query: str, session_type: str, page: int, limit: int) -> List[Dict]:
        logger.debug("search_sessions skipped (archived)")
        return []

    def count_search_results(self, user_id: int, query: str, session_type: str) -> int:
        logger.debug("count_search_results skipped (archived)")
        return 0

    # Messages
    def add_message(self, session_id: int, message_payload: Dict) -> Optional[int]:
        logger.debug("add_message skipped (archived)")
        return None


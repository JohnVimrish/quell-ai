from __future__ import annotations

import logging
from typing import Dict, List, Optional

from api.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ContactsRepository(BaseRepository):
    """Archived placeholder. All operations are disabled and return safe defaults."""

    def __init__(self, database_url: str, queries_config: Dict | None = None):
        super().__init__(database_url, queries_config or {})
        self._disabled = True
        logger.info("ContactsRepository is archived/disabled")

    def create_contact(self, contact_data: Dict) -> Optional[int]:
        logger.debug("create_contact skipped (archived)")
        return None

    def update_contact(self, contact_id: int, update_data: Dict) -> bool:
        logger.debug("update_contact skipped (archived)")
        return False

    def get_contact(self, contact_id: int, user_id: int | None = None) -> Optional[Dict]:
        logger.debug("get_contact skipped (archived)")
        return None

    def get_by_phone(self, user_id: int, phone_number: str) -> Optional[Dict]:
        logger.debug("get_by_phone skipped (archived)")
        return None

    def get_contact_by_phone(self, phone_number: str, user_id: int) -> Optional[Dict]:
        return self.get_by_phone(user_id, phone_number)

    def get_contacts(self, user_id: int, filters: Dict | None = None) -> List[Dict]:
        logger.debug("get_contacts skipped (archived)")
        return []


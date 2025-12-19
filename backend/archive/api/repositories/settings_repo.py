from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class SettingsRepository:
    """Archived placeholder for user settings operations."""

    def __init__(self, database_url: str, *_: object, **__: object):
        self.database_url = database_url
        logger.info("SettingsRepository is archived/disabled")

    def get_settings(self, user_id: int) -> Dict:
        logger.debug("get_settings skipped (archived); returning defaults")
        return {
            "user_id": user_id,
            "notifications": {},
            "preferences": {},
        }

    def update_settings(self, user_id: int, payload: Dict) -> Dict:
        logger.debug("update_settings skipped (archived); echoing payload")
        base = self.get_settings(user_id)
        base.update(payload or {})
        return base


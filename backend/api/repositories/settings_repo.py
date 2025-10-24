from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from functionalities.settings import UserSettings


class SettingsRepository:
    """Repository for managing per-user assistant settings."""

    def __init__(self, database_url: str):
        self._engine = create_engine(database_url, future=True)
        self._session_factory = sessionmaker(
            bind=self._engine, autoflush=False, expire_on_commit=False
        )

    @contextmanager
    def _session_scope(self):
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_settings(self, user_id: int) -> Dict:
        with self._session_scope() as sess:
            settings = (
                sess.query(UserSettings)
                .filter(UserSettings.user_id == user_id)
                .first()
            )
            if not settings:
                settings = UserSettings(user_id=user_id)
                sess.add(settings)
                sess.flush()
            return settings.to_dict()

    def update_settings(self, user_id: int, payload: Dict) -> Dict:
        with self._session_scope() as sess:
            settings = (
                sess.query(UserSettings)
                .filter(UserSettings.user_id == user_id)
                .first()
            )
            if not settings:
                settings = UserSettings(user_id=user_id)
                sess.add(settings)

            for key, value in payload.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

            return settings.to_dict()


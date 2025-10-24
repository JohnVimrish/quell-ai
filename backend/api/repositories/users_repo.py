from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


@dataclass
class User:
    id: Optional[int]
    email: str
    password_hash: str
    phone_number: Optional[str] = None
    is_active: bool = True
    email_verified: bool = False
    phone_verified: bool = False
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


@dataclass
class UserSettings:
    id: Optional[int]
    user_id: int
    sms_forwarding_number: Optional[str] = None
    call_forwarding_number: Optional[str] = None
    ai_mode_enabled: bool = True
    ai_mode_expires_at: Optional[str] = None
    spam_filtering_enabled: bool = True
    recording_enabled: bool = False
    transcript_enabled: bool = False
    voice_cloning_enabled: bool = False
    timezone: str = 'UTC'
    language_code: str = 'en'


class UsersRepository:
    """Repository for user management operations using SQLAlchemy Core."""

    def __init__(self, database_url: Optional[str] = None, queries_config: Optional[Dict[str, Any]] = None):
        # Resolve config if not provided
        if database_url is None or queries_config is None:
            try:
                from flask import current_app
                cfg = current_app.config.get("APP_CONFIG") if current_app else None
                if database_url is None and cfg:
                    database_url = getattr(cfg, 'database_url', None)
                if queries_config is None and cfg:
                    queries_config = getattr(cfg, 'queries', None)
            except Exception:
                pass
            if database_url is None or queries_config is None:
                from api.utils.config import Config
                _cfg = Config.load()
                database_url = database_url or _cfg.database_url
                queries_config = queries_config or _cfg.queries

        self.engine = create_engine(database_url, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False, future=True)
        self.queries = queries_config or {}

    def _exec(self, sql_key: str, params: Optional[list] = None, expect_rows: bool = True):
        """Execute a users.* query from queries.json with proper bind conversion.

        - Converts Postgres-style placeholders ($1, $2, ...) to named binds (:p1, :p2, ...)
        - Accepts params as list/tuple or dict
        """
        raw_sql = self.queries["users"][sql_key]

        # Build SQLAlchemy-compatible SQL and bind map
        bind_map: Dict[str, Any]
        sql = raw_sql
        if isinstance(params, (list, tuple)):
            # Convert $1 -> :p1, $2 -> :p2, ...
            sql = re.sub(r"\$(\d+)", lambda m: f":p{m.group(1)}", raw_sql)
            bind_map = {f"p{i+1}": v for i, v in enumerate(params)}
        elif isinstance(params, dict):
            bind_map = params
        else:
            bind_map = {}

        with self.engine.begin() as conn:
            result = conn.execute(text(sql), bind_map)
            if expect_rows:
                return [dict(row) for row in result.mappings().all()]
            return None

    def create_user(self, email: str, password_hash: str, phone_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        rows = self._exec("create", [email, password_hash, phone_number])
        return rows[0] if rows else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        rows = self._exec("get_by_id", [user_id])
        return rows[0] if rows else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        rows = self._exec("get_by_email", [email])
        return rows[0] if rows else None

    def get_user_by_email_for_login(self, email: str) -> Optional[Dict[str, Any]]:
        rows = self._exec("get_by_email_for_login", [email])
        return rows[0] if rows else None

    def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        rows = self._exec("get_by_phone", [phone_number])
        return rows[0] if rows else None

    def update_last_login(self, user_id: int) -> bool:
        self._exec("update_last_login", [user_id], expect_rows=False)
        return True

    def update_password(self, user_id: int, password_hash: str) -> bool:
        self._exec("update_password", [user_id, password_hash], expect_rows=False)
        return True

    def update_profile(self, user_id: int, email: str, phone_number: Optional[str]) -> bool:
        self._exec("update_profile", [user_id, email, phone_number], expect_rows=False)
        return True

    def verify_email(self, user_id: int) -> bool:
        self._exec("verify_email", [user_id], expect_rows=False)
        return True

    def verify_phone(self, user_id: int) -> bool:
        self._exec("verify_phone", [user_id], expect_rows=False)
        return True

    def deactivate_user(self, user_id: int) -> bool:
        self._exec("deactivate", [user_id], expect_rows=False)
        return True

    def activate_user(self, user_id: int) -> bool:
        self._exec("activate", [user_id], expect_rows=False)
        return True

    def delete_user(self, user_id: int) -> bool:
        self._exec("delete", [user_id], expect_rows=False)
        return True

    def check_email_exists(self, email: str) -> bool:
        rows = self._exec("check_email_exists", [email])
        return (rows[0]["count"] if rows and "count" in rows[0] else rows[0][0]) > 0 if rows else False

    def check_phone_exists(self, phone_number: str) -> bool:
        rows = self._exec("check_phone_exists", [phone_number])
        return (rows[0]["count"] if rows and "count" in rows[0] else rows[0][0]) > 0 if rows else False

    def create_user_settings(self, user_id: int, **settings) -> Optional[Dict[str, Any]]:
        rows = self._exec(
            "user_settings.create",
            [
                user_id,
                settings.get('sms_forwarding_number'),
                settings.get('call_forwarding_number'),
                settings.get('ai_mode_enabled', True),
                settings.get('spam_filtering_enabled', True),
                settings.get('recording_enabled', False),
                settings.get('transcript_enabled', False),
                settings.get('voice_cloning_enabled', False),
                settings.get('timezone', 'UTC'),
                settings.get('language_code', 'en'),
            ],
        )
        return rows[0] if rows else None

    def get_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        rows = self._exec("user_settings.get_by_user", [user_id])
        return rows[0] if rows else None

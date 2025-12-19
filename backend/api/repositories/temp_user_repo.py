from __future__ import annotations

import os
from typing import Dict, Optional

from werkzeug.security import generate_password_hash

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from api.repositories.users_repo import UsersRepository

DEFAULT_LAB_EMAIL = os.getenv("LAB_DUMMY_EMAIL_BASE", "dummy_user@quell-ai.com")
DEFAULT_LAB_PASSWORD = os.getenv("LAB_DUMMY_PASSWORD", "ConversationLab#123")


class TempUserRepository:
    """Repository for managing temporary Conversation Lab users."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False, future=True)
        self._users_repo = UsersRepository(database_url)
        self._ensure_table()

    def _ensure_table(self) -> None:
        ddl = text(
            """
            CREATE TABLE IF NOT EXISTS ai_intelligence.conversation_lab_temp_users (
                id BIGSERIAL PRIMARY KEY,
                session_id VARCHAR(64) UNIQUE NOT NULL,
                display_name VARCHAR(255),
                ip_hint VARCHAR(128),
                backing_user_id BIGINT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        with self.engine.begin() as conn:
            conn.execute(ddl)
            conn.execute(
                text(
                    """
                    ALTER TABLE ai_intelligence.conversation_lab_temp_users
                    ADD COLUMN IF NOT EXISTS backing_user_id BIGINT
                    """
                )
            )

    def _set_backing_user(self, user_id: int, backing_id: int) -> None:
        sql = text(
            """
            UPDATE ai_intelligence.conversation_lab_temp_users
            SET backing_user_id = :backing
            WHERE id = :user_id
            """
        )
        with self.engine.begin() as conn:
            conn.execute(sql, {"backing": backing_id, "user_id": user_id})

    def _build_dummy_email(self, session_id: str) -> str:
        base = DEFAULT_LAB_EMAIL or "lab_user@quell-ai.com"
        local, _, domain = base.partition("@")
        if not domain:
            domain = "quell-ai.com"
        safe_session = "".join(ch for ch in session_id if ch.isalnum())[:40] or "lab"
        return f"{local}+{safe_session}@{domain}".lower()

    def _create_backing_account(self, email: str, display_name: Optional[str]) -> Optional[int]:
        name = (display_name or "Conversation Lab User").strip() or "Conversation Lab User"
        insert_sql = text(
            """
            INSERT INTO user_management.users (
                email,
                password_hash,
                name,
                phone_number,
                is_active,
                email_verified,
                phone_verified,
                account_status,
                timezone,
                language_code,
                email_notifications,
                sms_notifications,
                marketing_consent,
                data_processing_consent,
                consent_given_at,
                created_by,
                updated_by
            )
            VALUES (
                :email,
                :password_hash,
                :name,
                NULL,
                TRUE,
                FALSE,
                FALSE,
                'active',
                'UTC',
                'en',
                TRUE,
                FALSE,
                FALSE,
                TRUE,
                NOW(),
                'conversation_lab',
                'conversation_lab'
            )
            RETURNING id
            """
        )
        password_hash = generate_password_hash(DEFAULT_LAB_PASSWORD)
        try:
            with self.engine.begin() as conn:
                row = conn.execute(
                    insert_sql, {"email": email, "password_hash": password_hash, "name": name}
                ).mappings().first()
            return int(row["id"]) if row and row.get("id") is not None else None
        except IntegrityError:
            with self.engine.begin() as conn:
                row = conn.execute(
                    text("SELECT id FROM user_management.users WHERE email = :email"), {"email": email}
                ).mappings().first()
            return int(row["id"]) if row and row.get("id") is not None else None

    def _ensure_backing_user(self, user: Dict[str, Optional[str]]) -> Optional[int]:
        existing = user.get("backing_user_id")
        if existing:
            return int(existing)
        session_id = user.get("session_id")
        if not session_id:
            return None
        email = self._build_dummy_email(session_id)
        account = self._users_repo.get_user_by_email(email)
        if not account:
            backing_id = self._create_backing_account(email, user.get("display_name"))
            if backing_id:
                try:
                    self._users_repo.create_user_settings(backing_id)
                except Exception:
                    pass
        else:
            backing_id = int(account["id"]) if account.get("id") is not None else None
        if backing_id:
            self._set_backing_user(int(user["id"]), backing_id)
            user["backing_user_id"] = backing_id
        return backing_id

    def create_user(
        self,
        session_id: str,
        *,
        display_name: Optional[str] = None,
        ip_hint: Optional[str] = None,
    ) -> Dict[str, Optional[str]]:
        sql = text(
            """
            INSERT INTO ai_intelligence.conversation_lab_temp_users (session_id, display_name, ip_hint)
            VALUES (:session_id, :display_name, :ip_hint)
            RETURNING id, session_id, display_name, backing_user_id
            """
        )
        with self.engine.begin() as conn:
            row = conn.execute(
                sql,
                {"session_id": session_id, "display_name": display_name, "ip_hint": ip_hint},
            ).mappings().first()
            data = dict(row) if row else {}
        if data:
            self._ensure_backing_user(data)
        return data

    def get_user(self, user_id: int) -> Optional[Dict[str, Optional[str]]]:
        sql = text(
            """
            SELECT id, session_id, display_name, backing_user_id
            FROM ai_intelligence.conversation_lab_temp_users
            WHERE id = :user_id
            """
        )
        with self.engine.begin() as conn:
            row = conn.execute(sql, {"user_id": user_id}).mappings().first()
        data = dict(row) if row else None
        if data:
            self._ensure_backing_user(data)
        return data

    def update_name(self, user_id: int, display_name: str) -> Optional[Dict[str, Optional[str]]]:
        sql = text(
            """
            UPDATE ai_intelligence.conversation_lab_temp_users
            SET display_name = :display_name
            WHERE id = :user_id
            RETURNING id, session_id, display_name, backing_user_id
            """
        )
        with self.engine.begin() as conn:
            row = conn.execute(sql, {"user_id": user_id, "display_name": display_name}).mappings().first()
        data = dict(row) if row else None
        if data:
            self._ensure_backing_user(data)
        return data

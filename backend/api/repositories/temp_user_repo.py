from __future__ import annotations

from typing import Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class TempUserRepository:
    """Repository for managing temporary Conversation Lab users."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False, future=True)
        self._ensure_table()

    def _ensure_table(self) -> None:
        ddl = text(
            """
            CREATE TABLE IF NOT EXISTS ai_intelligence.conversation_lab_temp_users (
                id BIGSERIAL PRIMARY KEY,
                session_id VARCHAR(64) UNIQUE NOT NULL,
                display_name VARCHAR(255),
                ip_hint VARCHAR(128),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
        with self.engine.begin() as conn:
            conn.execute(ddl)

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
            RETURNING id, session_id, display_name
            """
        )
        with self.engine.begin() as conn:
            row = conn.execute(
                sql,
                {"session_id": session_id, "display_name": display_name, "ip_hint": ip_hint},
            ).mappings().first()
            return dict(row) if row else {}

    def get_user(self, user_id: int) -> Optional[Dict[str, Optional[str]]]:
        sql = text(
            """
            SELECT id, session_id, display_name
            FROM ai_intelligence.conversation_lab_temp_users
            WHERE id = :user_id
            """
        )
        with self.engine.begin() as conn:
            row = conn.execute(sql, {"user_id": user_id}).mappings().first()
            return dict(row) if row else None

    def update_name(self, user_id: int, display_name: str) -> Optional[Dict[str, Optional[str]]]:
        sql = text(
            """
            UPDATE ai_intelligence.conversation_lab_temp_users
            SET display_name = :display_name
            WHERE id = :user_id
            RETURNING id, session_id, display_name
            """
        )
        with self.engine.begin() as conn:
            row = conn.execute(sql, {"user_id": user_id, "display_name": display_name}).mappings().first()
            return dict(row) if row else None

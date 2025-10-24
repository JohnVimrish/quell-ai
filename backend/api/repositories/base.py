from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from api.utils.logging import get_logger
import time as time


class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


class BaseRepository:
    """SQLAlchemy-based repository base with helpers for text queries and sessions."""

    def __init__(self, database_url: str, queries_config: Optional[Dict[str, Dict[str, str]]] = None):
        self.database_url = database_url
        self.logger = get_logger(f"repository.{self.__class__.__name__}")
        self.engine = create_engine(database_url, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False, future=True)
        self.queries = queries_config or {}
    print('Problem')
    @contextmanager
    def get_session(self) -> Session:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _prepare_sql(self, sql: str, params: Optional[List[Any]]):
        """Translate Postgres $1..$n placeholders to SQLAlchemy named binds (:p1..:pn)."""
        if not params:
            return sql, {}
        bind_map: Dict[str, Any] = {}
        sql_conv = sql
        for i, value in enumerate(params, start=1):
            key = f"p{i}"
            sql_conv = sql_conv.replace(f"${i}", f":{key}")
            bind_map[key] = value
        return sql_conv, bind_map

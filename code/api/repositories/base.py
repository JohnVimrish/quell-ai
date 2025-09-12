from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import sqlite3
import psycopg
from api.utils.logging import get_logger
import time as time

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass

class BaseRepository:
    """Base repository class with database abstraction."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.logger = get_logger(f"repository.{self.__class__.__name__}")
        self._connection = None
        self._db_type = self._detect_db_type()
    
    def _detect_db_type(self) -> str:
        """Detect database type from URL."""
        if not self.database_url:
            return "sqlite"
        
        parsed = urlparse(self.database_url)
        scheme = parsed.scheme.lower()
        
        if scheme.startswith('postgresql') or scheme.startswith('postgres'):
            return "postgresql"
        elif scheme.startswith('sqlite'):
            return "sqlite"
        else:
            return "sqlite"  # Default fallback
    
    def _get_connection_params(self) -> Dict[str, Any]:
        """Extract connection parameters from database URL."""
        parsed = urlparse(self.database_url)
        params = {}
        
        if self._db_type == "postgresql":
            params["host"] = parsed.hostname
            params["port"] = parsed.port or 5432
            params["database"] = parsed.path[1:] if parsed.path else None
            params["user"] = parsed.username
            params["password"] = parsed.password
        elif self._db_type == "sqlite":
            params["database"] = parsed.path if parsed.path else ":memory:"
        
        return params
    
    def get_connection(self):
        """Get database connection based on type."""
        if self._connection:
            return self._connection
            
        try:
            if self._db_type == "postgresql":
                conn_params = self._get_connection_params()
                self._connection = psycopg.connect(**conn_params)
            elif self._db_type == "sqlite":
                conn_params = self._get_connection_params()
                self._connection = sqlite3.connect(conn_params["database"])
            
            return self._connection
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
    
    def execute(self, query: str, params: Optional[List[Any]] = None) -> Optional[List[Any]]:
        """Execute a database query."""
        start = time.perf_counter()
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            self.logger.info(
                "db_query_start",
                extra={"event": "db_query_start", "query": query, "param_count": len(params or [])},
            )
            
            cursor.execute(query, params or [])
            
            # Handle different types of queries
            if query.strip().upper().startswith(('SELECT', 'WITH')):
                rows = cursor.fetchall()
                row_count = len(rows)
                result = rows
            else:
                row_count = cursor.rowcount
                result = None
                
            conn.commit()
            dur = int((time.perf_counter() - start) * 1000)
            self.logger.info(
                "db_query_ok",
                extra={"event": "db_query_ok", "query": query, "duration_ms": dur, "row_count": row_count},
            )
            return result
            
        except Exception as e:
            dur = int((time.perf_counter() - start) * 1000)
            self.logger.exception(
                "db_query_failed",
                extra={"event": "db_query_failed", "query": query, "duration_ms": dur},
            )
            if conn:
                conn.rollback()
            raise
        finally:
            if conn and self._db_type == "sqlite":
                # For SQLite, we close the connection after each operation
                conn.close()
                self._connection = None

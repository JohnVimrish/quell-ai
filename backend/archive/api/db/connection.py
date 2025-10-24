import logging
from contextlib import contextmanager

try:
    # psycopg3 connection pool
    from psycopg_pool import ConnectionPool  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    ConnectionPool = None  # type: ignore

class DatabaseManager:
    def __init__(self, database_url):
        self.database_url = database_url
        self.pool = None
        self.logger = logging.getLogger(__name__)
        if ConnectionPool is None:
            self.logger.warning(
                "psycopg_pool (psycopg3) is archived; prefer SQLAlchemy elsewhere"
            )
            self.pool = None
        else:
            self._initialize_pool()
    
    def _initialize_pool(self):
        if ConnectionPool is None:
            self.logger.warning("psycopg_pool unavailable; skipping pool init")
            self.pool = None
            return

        try:
            self.pool = ConnectionPool(
                conninfo=self.database_url,
                min_size=1,
                max_size=20,
                timeout=30,
            )
            self.logger.info("Database connection pool (psycopg3) initialized [archived]")
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            self.pool = None
            raise
    
    @contextmanager
    def get_connection(self):
        if not self.pool:
            raise RuntimeError("Database connection pool is not available")
        with self.pool.connection() as conn:  # type: ignore[attr-defined]
            yield conn
    
    def test_connection(self):
        if not self.pool:
            self.logger.warning("Database pool not initialised; treating as unavailable")
            return False
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1
    
    def close_all_connections(self):
        if not self.pool:
            self.logger.debug("No database pool to close")
            return
        try:
            self.pool.close()  # type: ignore[union-attr]
            self.pool = None
            self.logger.info("Database connection pool closed [archived]")
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Failed to close database pool: {exc}")


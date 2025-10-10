import logging
from contextlib import contextmanager

try:
    import psycopg2  # type: ignore
    from psycopg2.pool import ThreadedConnectionPool  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    psycopg2 = None
    ThreadedConnectionPool = None

class DatabaseManager:
    def __init__(self, database_url):
        self.database_url = database_url
        self.pool = None
        self.logger = logging.getLogger(__name__)
        if ThreadedConnectionPool is None:
            self.logger.warning(
                "psycopg2 is not installed; database features will be disabled"
            )
            self.pool = None
        else:
            self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        if ThreadedConnectionPool is None:
            self.logger.warning("ThreadedConnectionPool unavailable; skipping pool init")
            self.pool = None
            return

        try:
            self.pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=self.database_url
            )
            self.logger.info("Database connection pool initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            self.pool = None
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            raise RuntimeError("Database connection pool is not available")

        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def test_connection(self):
        """Test database connectivity"""
        if not self.pool:
            self.logger.warning("Database pool not initialised; treating as unavailable")
            return False

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1

    def close_all_connections(self):
        """Close all pooled connections."""
        if not self.pool:
            self.logger.debug("No database pool to close")
            return

        try:
            self.pool.closeall()
            self.pool = None
            self.logger.info("Database connection pool closed")
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Failed to close database pool: {exc}")

import logging
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, database_url):
        self.database_url = database_url
        self.pool = None
        self.logger = logging.getLogger(__name__)
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=20,
                dsn=self.database_url
            )
            self.logger.info("Database connection pool initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def test_connection(self):
        """Test database connectivity"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1
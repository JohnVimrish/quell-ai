import psycopg
from contextlib import contextmanager
from api.utils.logging import logger

@contextmanager
def get_conn(db_url: str):
    logger.info("db_connect_start", extra={"event": "db_connect_start"})
    try:
        conn = psycopg.connect(db_url)
        logger.info("db_connect_ok", extra={"event": "db_connect_ok"})
    except Exception:
        # Include no secrets in logs
        logger.exception("db_connect_failed", extra={"event": "db_connect_failed"})
        raise
    try:
        yield conn
    finally:
        try:
            conn.close()
            logger.info("db_connect_closed", extra={"event": "db_connect_closed"})
        except Exception:
            logger.warning("db_connect_close_failed", extra={"event": "db_connect_close_failed"})

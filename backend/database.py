"""
데이터베이스 연결 관리 모듈
"""

import os
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
import threading

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL 환경변수가 설정되지 않았습니다. "
        "예: export DATABASE_URL='postgresql://user@localhost:5432/odin_db'"
    )

_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    """커넥션 풀 lazy init - 최초 호출 시 풀 생성 (Double-Check Locking)"""
    global _pool
    # First check without lock (optimization)
    if _pool is None or _pool.closed:
        # Acquire lock for thread-safe initialization
        with _pool_lock:
            # Second check with lock to prevent race condition
            if _pool is None or _pool.closed:
                _pool = ThreadedConnectionPool(
                    minconn=2,
                    maxconn=10,
                    dsn=DATABASE_URL
                )
                logger.info("DB connection pool initialized (min=2, max=10)")
    return _pool


@contextmanager
def get_db_connection():
    """데이터베이스 연결 컨텍스트 매니저 (풀에서 연결 획득/반환)"""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        pool.putconn(conn)


def get_db():
    """FastAPI 의존성 주입용 데이터베이스 세션 (풀에서 연결 획득/반환)"""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        pool.putconn(conn)


def close_pool():
    """애플리케이션 종료 시 커넥션 풀 전체 반환"""
    global _pool
    if _pool and not _pool.closed:
        _pool.closeall()
        _pool = None
        logger.info("DB connection pool closed")

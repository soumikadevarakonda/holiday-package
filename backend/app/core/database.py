"""SQLAlchemy engine + per-request connection dependency.

SQLAlchemy Core (no ORM). Repositories take a `Connection` and run `text()` or table statements.
"""

import time
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection

from app.core.config import get_settings

_engine: Engine | None = None
_last_ping_time: float = 0.0
_last_ping_result: bool = False


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_settings().DB_URL,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={"connect_timeout": 1},
        )
    return _engine


def get_db() -> Iterator[Connection]:
    """FastAPI dependency: one transaction per request, committed on success, rolled back on error."""
    with get_engine().begin() as conn:
        yield conn


def db_ping() -> bool:
    global _last_ping_time, _last_ping_result
    now = time.time()
    # Cache negative ping for 2 seconds to avoid stacking blocking socket timeouts
    if not _last_ping_result and (now - _last_ping_time < 2.0):
        return False

    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        _last_ping_result = True
    except Exception:
        _last_ping_result = False
    _last_ping_time = now
    return _last_ping_result

"""SQLAlchemy engine + per-request connection dependency.

SQLAlchemy Core (no ORM). Repositories take a `Connection` and run `text()` or table statements.
"""

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import Connection

from app.core.config import get_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_settings().DB_URL,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={"connect_timeout": 5},
        )
    return _engine


def get_db() -> Iterator[Connection]:
    """FastAPI dependency: one transaction per request, committed on success, rolled back on error."""
    with get_engine().begin() as conn:
        yield conn


def db_ping() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

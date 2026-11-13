"""SQLAlchemy engine, ORM session factory and the per-request session dependency.

- Catalog seeding and migrations use the engine directly (SQLAlchemy Core).
- The API's repositories use ORM sessions from get_db(): one transaction per request,
  committed on success and rolled back on any error.
"""

from __future__ import annotations

import time
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_last_ping_time: float = 0.0
_last_ping_result: bool = False


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = get_settings().DB_URL
        kwargs = {"connect_args": {"connect_timeout": 1}} if url.startswith("mysql") else {}
        _engine = create_engine(url, pool_pre_ping=True, pool_recycle=1800, **kwargs)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False,
                                        expire_on_commit=False)
    return _session_factory


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one ORM session per request; commit on success, roll back on error."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def db_ping() -> bool:
    global _last_ping_time, _last_ping_result
    now = time.time()
    # Cache a failed ping for 2 seconds so health checks don't stack blocking socket timeouts
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

"""
Database engine, session factory, and connection management for Build My Holiday.

Built on SQLAlchemy 2.0 with connection pooling and clear error diagnostics.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from database.config import DatabaseConfig, get_db_config

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when connecting to or communicating with the database fails."""


# Module-level singletons for reusable engine and session factory
_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def create_db_engine(config: DatabaseConfig | None = None, echo: bool = False) -> Engine:
    """
    Create a new SQLAlchemy engine from configuration with connection pooling.
    Handles dialect specifics (e.g. MySQL vs SQLite in tests).
    """
    cfg = config or get_db_config()
    url = cfg.get_url()
    pool_kwargs = cfg.get_pool_kwargs()

    try:
        engine = create_engine(
            url,
            echo=echo,
            future=True,
            **pool_kwargs,
        )
        return engine
    except Exception as exc:
        raise DatabaseConnectionError(
            f"Failed to initialize database engine for URL '{url}': {exc}"
        ) from exc


def get_engine(config: DatabaseConfig | None = None, reset: bool = False) -> Engine:
    """
    Get or create the global singleton database engine.
    Pass reset=True to force re-creation (useful during configuration updates or tests).
    """
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is None or reset:
        if _ENGINE is not None:
            _ENGINE.dispose()
        _ENGINE = create_db_engine(config=config)
        _SESSION_FACTORY = None
    return _ENGINE


def get_session_factory(
    engine: Engine | None = None, reset: bool = False
) -> sessionmaker[Session]:
    """
    Get or create the global session factory (sessionmaker) bound to the engine.
    """
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None or reset:
        eng = engine or get_engine()
        _SESSION_FACTORY = sessionmaker(
            bind=eng,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SESSION_FACTORY


@contextmanager
def get_db_session(
    factory: sessionmaker[Session] | None = None,
) -> Generator[Session, None, None]:
    """
    Transactional session context manager.
    Yields a Session, automatically commits if no exception is raised,
    rolls back on error, and always closes the session upon exit.
    """
    maker = factory or get_session_factory()
    session = maker()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error("Session transaction failed and was rolled back: %s", exc)
        raise
    finally:
        session.close()


def check_connection(engine: Engine | None = None) -> bool:
    """
    Ping the database by executing 'SELECT 1'.
    Returns True if successful, or raises DatabaseConnectionError with context.
    """
    eng = engine or get_engine()
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except (OperationalError, SQLAlchemyError) as exc:
        raise DatabaseConnectionError(
            f"Database health check failed: could not connect to database: {exc}"
        ) from exc
    except Exception as exc:
        raise DatabaseConnectionError(
            f"Unexpected error during database health check: {exc}"
        ) from exc


def dispose_engine() -> None:
    """Dispose of the global engine connection pool."""
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is not None:
        _ENGINE.dispose()
        _ENGINE = None
    _SESSION_FACTORY = None

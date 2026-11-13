"""
Database session management and FastAPI dependency.
"""

from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy.orm import Session

from database.connection import check_connection, get_db_session, get_engine
from database.models import Base

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create all registered application tables if they do not exist."""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Application database tables verified/created successfully.")
    except Exception as exc:
        logger.warning("Could not auto-create tables: %s", exc)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides an isolated transactional database session.
    Automatically commits on normal completion and rolls back on exception.
    """
    with get_db_session() as session:
        yield session


def is_database_connected() -> bool:
    """Check database health, returning True if connected."""
    try:
        return check_connection()
    except Exception:
        return False

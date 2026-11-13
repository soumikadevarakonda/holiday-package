"""Shared pytest fixtures.

- The catalog loads from the JSON files (DB_AUTO_INIT=false), so engine tests need no MySQL.
- API tests get an app whose get_db() uses an in-memory SQLite database (her ORM models,
  Base.metadata.create_all), wiped after each test. MySQL is never touched.
"""

import os

os.environ["DB_AUTO_INIT"] = "false"  # unit / API tests manage the DB themselves

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.catalog.store import get_store  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Base  # noqa: E402
from tests.helpers import menon_package  # noqa: E402

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session")
def catalog_store():
    store = get_store()
    if not store.loaded:
        store.load()
    return store


@pytest.fixture
def db_session() -> Iterator[Session]:
    """Fresh tables per test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """App client: real engine, SQLite in memory for app state (commit per request, like get_db)."""
    app = create_app()

    def override_get_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:      # unexpected server errors fail the test with their traceback
        yield c


@pytest.fixture
def menon():
    return menon_package()

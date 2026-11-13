"""Shared pytest fixtures.

An app client (no DB init, so tests run without MySQL), the catalog store and the Menon fixture package.
"""

import os

os.environ["DB_AUTO_INIT"] = "false"  # unit / API tests manage the DB themselves

from app.core.config import get_settings

get_settings.cache_clear()

import pytest
from fastapi.testclient import TestClient

from app.catalog.store import get_store
from app.main import create_app
from tests.helpers import menon_package


@pytest.fixture(scope="session")
def catalog_store():
    store = get_store()
    if not store.loaded:
        store.load()
    return store


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def menon():
    return menon_package()

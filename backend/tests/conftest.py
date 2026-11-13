"""Shared pytest fixtures.

Phase 0: an app client (no DB init, so tests run without MySQL) and the Menon fixture package.
Person A adds the real-catalog fixture at M-1.
"""

import os

os.environ.setdefault("DB_AUTO_INIT", "false")  # unit / API tests manage the DB themselves

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.stubs import menon_package


@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def menon():
    return menon_package()

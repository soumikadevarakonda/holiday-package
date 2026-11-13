"""
Pytest configuration and fixtures for Build My Holiday API tests.
Uses SQLite in-memory database and TestClient.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Force SQLite in-memory for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.app.core.database import get_db
from backend.app.core.engine_adapter import reset_engine_adapter, set_engine_adapter
from backend.app.main import app
from database.models import Base

# Setup test in-memory SQLite engine
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables in test in-memory SQLite DB once for session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a clean isolated transaction per test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ------------------------------------------------------------------------------
# Test Double: MockEngineAdapter for Contract Verification
# ------------------------------------------------------------------------------
@dataclass
class MockOption:
    catalog_id: str
    name: str
    price_diff: float
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "name": self.name,
            "price_diff": self.price_diff,
            "details": self.details,
        }


@dataclass
class MockBuildResult:
    outcome: str = "PACKAGE"
    package: dict[str, Any] = field(default_factory=dict)
    city_plans: list[dict[str, Any]] = field(default_factory=list)
    cheapest_total: float = 0.0
    over_by: float = 0.0
    suggestion: str = ""
    reason: str = ""


@dataclass
class MockChangeResult:
    package: dict[str, Any] = field(default_factory=dict)
    side_effects: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class MockEngineAdapter:
    """
    Contract test double implementing the 6 frozen engine interfaces.
    Returns valid mock data modeling the Menon family package.
    """

    def is_engine_available(self) -> bool:
        return True

    def build(self, req: Any, mode: str = "default") -> MockBuildResult:
        # Check budget for M8 test
        budget = getattr(req, "budget", 350000)
        if budget < 100000:
            return MockBuildResult(
                outcome="OVER_BUDGET",
                package={"total_inr": 219324, "items": []},
                cheapest_total=219324.0,
                over_by=float(219324 - budget),
                suggestion="Raise budget to ₹2,19,324 or reduce nights",
            )

        pkg_data = {
            "trip_id": "pkg-menon-demo",
            "country": getattr(req, "destination_country", "Japan"),
            "start_date": str(getattr(req, "start_date", "2027-04-10")),
            "end_date": "2027-04-16",
            "budget_inr": int(budget),
            "total_inr": 101640,
            "items": [
                {
                    "item_id": "i1",
                    "type": "flight",
                    "name": "AV 520 BLR to NRT",
                    "city": "Tokyo",
                    "status": "PLANNED",
                    "catalog_id": "FL-401",
                    "start": "2027-04-09T23:50",
                    "end": "2027-04-10T10:30",
                    "quantity": 3,
                    "price_inr": 75600,
                    "warnings": [],
                },
                {
                    "item_id": "i2",
                    "type": "hotel",
                    "name": "Ginza Willow Hotel",
                    "city": "Tokyo",
                    "status": "PLANNED",
                    "catalog_id": "HTL-TYO-002",
                    "room_id": "RM-TYO-002-A",
                    "start": "2027-04-10",
                    "end": "2027-04-13",
                    "quantity": 1,
                    "price_inr": 26040,
                    "warnings": [],
                },
            ],
        }
        city_plans = [
            {"plan_id": "p1", "cities": ["Tokyo", "Kyoto"], "nights": [3, 3], "label": "Tokyo (3N) -> Kyoto (3N)"},
            {"plan_id": "p2", "cities": ["Tokyo"], "nights": [6], "label": "Tokyo (6N)"},
        ]
        return MockBuildResult(outcome="PACKAGE", package=pkg_data, city_plans=city_plans)

    def rebuild(self, req: Any, city_plan: Any) -> MockBuildResult:
        pkg_data = dict(req if isinstance(req, dict) else {})
        pkg_data["total_inr"] = 115000
        return MockBuildResult(outcome="PACKAGE", package=pkg_data)

    def validate(self, pkg: Any) -> list[Any]:
        # Return empty list indicating package passes all rules
        return []

    def options(self, pkg: Any, kind: str, **params: Any) -> list[MockOption]:
        if kind == "hotel":
            return [
                MockOption(catalog_id="HTL-TYO-002", name="Ginza Willow Hotel", price_diff=2500.0),
                MockOption(catalog_id="HTL-TYO-003", name="Asakusa River Hotel", price_diff=-1800.0),
            ]
        elif kind == "flight":
            return [
                MockOption(catalog_id="FL-702", name="AirVeda AV 771", price_diff=-4200.0),
            ]
        elif kind == "attraction":
            return [
                MockOption(catalog_id="ATT-TYO-001", name="Tokyo Skytree", price_diff=1500.0),
            ]
        return []

    def apply_change(self, pkg: Any, change: Any) -> MockChangeResult:
        new_pkg = dict(pkg)
        new_items = list(new_pkg.get("items", []))
        new_catalog_id = change.get("new_catalog_id", "NEW-ID")
        kind = change.get("kind", "hotel")

        # Swap catalog_id on matching item
        for it in new_items:
            if it.get("type") == kind:
                it["catalog_id"] = new_catalog_id
                it["price_inr"] = it.get("price_inr", 0) + 2000
                break

        new_pkg["items"] = new_items
        new_pkg["total_inr"] = sum(it.get("price_inr", 0) for it in new_items)
        return MockChangeResult(package=new_pkg, side_effects=["Airport transfer re-timed"], warnings=[])

    def get_store(self) -> Any:
        return None


@pytest.fixture
def mock_engine() -> Generator[MockEngineAdapter, None, None]:
    """Inject MockEngineAdapter for the duration of a test."""
    adapter = MockEngineAdapter()
    set_engine_adapter(adapter)
    yield adapter
    reset_engine_adapter()

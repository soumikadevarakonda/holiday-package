"""
API tests for Package Lifecycle Endpoints:
- POST /api/packages (Endpoint 4)
- GET /api/packages/{package_id} (Endpoint 5)
- GET /api/packages/{package_id}/city-plans (Endpoint 10)
- POST /api/packages/{package_id}/rebuild (Endpoint 11)
- POST /api/packages/{package_id}/undo (Endpoint 12)
"""

from fastapi.testclient import TestClient

MENON_REQUEST_PAYLOAD = {
    "origin": "BLR",
    "destination_country": "Japan",
    "start_date": "2027-04-10",
    "end_date": "2027-04-16",
    "travelers": {
        "adults": 2,
        "children": 1,
        "child_ages": [10],
    },
    "budget": 350000,
    "pace": "moderate",
    "interests": ["culture", "sightseeing"],
}


def test_build_package_engine_unavailable_by_default(client: TestClient):
    """When real engine is not installed, POST /api/packages returns 503."""
    response = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    assert response.status_code == 503
    data = response.json()
    assert data["code"] == "ENGINE_UNAVAILABLE"


def test_build_package_success_with_mock_engine(client: TestClient, mock_engine):
    """When engine is available, POST /api/packages builds and persists package version 1."""
    response = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    assert response.status_code == 201
    data = response.json()

    assert data["status"] in ("PLANNED", "DRAFT")
    assert data["version"] == 1
    assert "package_id" in data
    assert data["total_inr"] > 0
    assert len(data["items"]) > 0
    assert "timeline" in data
    assert len(data["timeline"]) > 0


def test_build_package_over_budget_scenario(client: TestClient, mock_engine):
    """When budget is too low, outcome is OVER_BUDGET with suggestion (M8)."""
    low_budget_payload = dict(MENON_REQUEST_PAYLOAD)
    low_budget_payload["budget"] = 50000

    response = client.post("/api/packages", json=low_budget_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "OVER_BUDGET"
    assert data["over_by"] > 0
    assert data["cheapest_total"] > 0
    assert "suggestion" in data


def test_build_package_validation_errors(client: TestClient):
    """Invalid input values must trigger 422 Unprocessable Entity."""
    # Negative budget
    invalid_budget = dict(MENON_REQUEST_PAYLOAD)
    invalid_budget["budget"] = -1000
    res = client.post("/api/packages", json=invalid_budget)
    assert res.status_code == 422

    # End date before start date
    invalid_dates = dict(MENON_REQUEST_PAYLOAD)
    invalid_dates["start_date"] = "2027-04-16"
    invalid_dates["end_date"] = "2027-04-10"
    res = client.post("/api/packages", json=invalid_dates)
    assert res.status_code == 422

    # 0 adults
    no_adults = dict(MENON_REQUEST_PAYLOAD)
    no_adults["travelers"] = {"adults": 0, "children": 1, "child_ages": [10]}
    res = client.post("/api/packages", json=no_adults)
    assert res.status_code == 422


def test_get_package_by_id(client: TestClient, mock_engine):
    """GET /api/packages/{package_id} retrieves persisted package and current version."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    assert create_res.status_code == 201
    pkg_id = create_res.json()["package_id"]

    get_res = client.get(f"/api/packages/{pkg_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["package_id"] == pkg_id
    assert data["version"] == 1
    assert data["status"] in ("PLANNED", "DRAFT")
    assert "timeline" in data


def test_get_nonexistent_package_returns_404(client: TestClient):
    """GET /api/packages/{package_id} with unknown ID returns 404."""
    res = client.get("/api/packages/non-existent-pkg-999")
    assert res.status_code == 404
    assert res.json()["code"] == "NOT_FOUND"


def test_get_city_plans(client: TestClient, mock_engine):
    """GET /api/packages/{package_id}/city-plans returns candidate plans."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    plans_res = client.get(f"/api/packages/{pkg_id}/city-plans")
    assert plans_res.status_code == 200
    data = plans_res.json()
    plans = data.get("city_plans") if isinstance(data, dict) else data
    assert isinstance(plans, list)
    assert len(plans) > 0
    assert "cities" in plans[0]


def test_rebuild_package_flow(client: TestClient, mock_engine):
    """POST /api/packages/{package_id}/rebuild creates a new version with selected plan."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    rebuild_payload = {
        "city_plan": {
            "plan_id": "p2",
            "cities": ["Tokyo"],
            "nights": [6],
        }
    }
    rebuild_res = client.post(f"/api/packages/{pkg_id}/rebuild", json=rebuild_payload)
    assert rebuild_res.status_code == 200
    rebuild_data = rebuild_res.json()
    assert rebuild_data["version"] == 2


def test_undo_package_flow(client: TestClient, mock_engine):
    """POST /api/packages/{package_id}/undo restores previous snapshot."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    # Trying undo on v1 should fail with 409 (PRD Section 10)
    undo_fail = client.post(f"/api/packages/{pkg_id}/undo")
    assert undo_fail.status_code == 409

    # Rebuild to create v2
    client.post(
        f"/api/packages/{pkg_id}/rebuild",
        json={"city_plan": {"plan_id": "p2", "cities": ["Tokyo"], "nights": [6]}},
    )

    # Now undo should succeed and create v3 matching v1 state
    undo_res = client.post(f"/api/packages/{pkg_id}/undo")
    assert undo_res.status_code == 200
    undo_data = undo_res.json()
    assert undo_data["version"] == 3


def test_persistence_across_separate_sessions(mock_engine):
    """Verify package, versions, and reservation persist across separate SQLAlchemy sessions."""
    from backend.tests.conftest import TestingSessionLocal
    from backend.app.packages.repository import PackageRepository
    from backend.app.reservations.repository import ReservationRepository
    from decimal import Decimal

    # Session 1: Create package and version
    s1 = TestingSessionLocal()
    pkg_repo1 = PackageRepository(s1)
    pkg = pkg_repo1.create_package(
        package_id="pkg-persist-test",
        initial_data={"country": "Japan", "items": [{"item_id": "i1", "type": "hotel", "catalog_id": "HTL-TYO-002"}]},
        total_price=Decimal("50000"),
    )
    s1.commit()
    s1.close()

    # Session 2: Read package back in fresh session, verify, and add version 2
    s2 = TestingSessionLocal()
    pkg_repo2 = PackageRepository(s2)
    loaded_pkg = pkg_repo2.get_package("pkg-persist-test")
    assert loaded_pkg is not None
    assert loaded_pkg.current_version_no == 1
    assert loaded_pkg.total_price == Decimal("50000")

    pkg_repo2.save_version(
        package_id="pkg-persist-test",
        snapshot={"country": "Japan", "items": [{"item_id": "i1", "type": "hotel", "catalog_id": "HTL-TYO-003"}]},
        change_summary="Swapped hotel",
        new_total_price=Decimal("52000"),
    )
    s2.commit()
    s2.close()

    # Session 3: Read version 2 back in fresh session, create reservation
    s3 = TestingSessionLocal()
    pkg_repo3 = PackageRepository(s3)
    res_repo3 = ReservationRepository(s3)
    v2_pkg = pkg_repo3.get_package("pkg-persist-test")
    assert v2_pkg.current_version_no == 2
    assert len(v2_pkg.versions) == 2

    res = res_repo3.create_reservation(
        package_id="pkg-persist-test",
        total_price=v2_pkg.total_price,
        package_snapshot=v2_pkg.current_version.snapshot,
    )
    v2_pkg.status = "BOOKED"
    s3.commit()
    ref = res.reference
    s3.close()

    # Session 4: Verify reservation persisted in new session
    s4 = TestingSessionLocal()
    res_repo4 = ReservationRepository(s4)
    loaded_res = res_repo4.get_by_reference(ref)
    assert loaded_res is not None
    assert loaded_res.package_id == "pkg-persist-test"
    assert loaded_res.status == "CONFIRMED"
    assert loaded_res.reference == ref
    s4.close()


def test_transaction_rollback_integrity():
    """Verify transactional rollback leaves no partial records."""
    from backend.tests.conftest import TestingSessionLocal
    from database.models.package import Package
    from decimal import Decimal

    s = TestingSessionLocal()
    try:
        pkg = Package(
            package_id="pkg-rollback-test",
            status="PLANNED",
            total_price=Decimal("10000"),
        )
        s.add(pkg)
        s.flush()
        # Force intentional failure by adding duplicate primary key
        dup = Package(
            package_id="pkg-rollback-test",
            status="PLANNED",
            total_price=Decimal("10000"),
        )
        s.add(dup)
        s.flush()
    except Exception:
        s.rollback()
    finally:
        s.close()

    # Verify nothing was committed
    verify_s = TestingSessionLocal()
    p = verify_s.get(Package, "pkg-rollback-test")
    assert p is None
    verify_s.close()

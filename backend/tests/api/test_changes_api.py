"""
API tests for Package Customization & Alternatives:
- GET /api/packages/{package_id}/options/hotel (Endpoint 6)
- GET /api/packages/{package_id}/options/flight (Endpoint 7)
- GET /api/packages/{package_id}/options/attraction (Endpoint 8)
- PATCH /api/packages/{package_id} (Endpoint 9)
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


def test_get_options_hotel(client: TestClient, mock_engine):
    """GET /api/packages/{package_id}/options/hotel returns candidate hotels with price diffs."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    res = client.get(f"/api/packages/{pkg_id}/options/hotel?city=Tokyo")
    assert res.status_code == 200
    data = res.json()
    assert "options" in data
    options = data["options"]
    assert isinstance(options, list)
    assert len(options) > 0
    assert "catalog_id" in options[0]
    assert "price_diff" in options[0]


def test_get_options_flight(client: TestClient, mock_engine):
    """GET /api/packages/{package_id}/options/flight returns candidate flights with price diffs."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    res = client.get(f"/api/packages/{pkg_id}/options/flight?leg=arrival")
    assert res.status_code == 200
    data = res.json()
    assert "options" in data
    options = data["options"]
    assert isinstance(options, list)
    assert len(options) > 0


def test_get_options_attraction(client: TestClient, mock_engine):
    """GET /api/packages/{package_id}/options/attraction returns candidate attractions."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    res = client.get(f"/api/packages/{pkg_id}/options/attraction?city=Tokyo")
    assert res.status_code == 200
    data = res.json()
    assert "options" in data
    options = data["options"]
    assert isinstance(options, list)
    assert len(options) > 0


def test_apply_change_creates_new_version(client: TestClient, mock_engine):
    """PATCH /api/packages/{package_id} swaps a component, increments version, tracks side effects."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]
    initial_version = create_res.json()["version"]

    change_payload = {
        "kind": "hotel",
        "action": "swap",
        "old_catalog_id": "HTL-TYO-001",
        "new_catalog_id": "HTL-TYO-002",
        "details": {"room_id": "RM-TYO-002-A"},
    }

    patch_res = client.patch(f"/api/packages/{pkg_id}", json=change_payload)
    assert patch_res.status_code == 200
    data = patch_res.json()

    assert data["version"] == initial_version + 1
    assert "side_effects" in data
    assert any("HTL-TYO-002" in str(item) for item in data["items"])


def test_apply_change_on_booked_package_fails(client: TestClient, mock_engine):
    """Modifying a package that has already been BOOKED must return 409 Conflict."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    # Confirm package
    confirm_res = client.post(
        f"/api/packages/{pkg_id}/confirm",
        json={"customer_name": "Rohan Menon", "customer_email": "rohan@example.com"},
    )
    assert confirm_res.status_code == 201

    # Attempt to modify
    change_payload = {
        "kind": "hotel",
        "action": "swap",
        "new_catalog_id": "HTL-TYO-002",
    }
    patch_res = client.patch(f"/api/packages/{pkg_id}", json=change_payload)
    assert patch_res.status_code == 409
    assert patch_res.json()["code"] == "CONFLICT"

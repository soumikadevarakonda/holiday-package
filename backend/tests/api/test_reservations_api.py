"""
API tests for Reservations & Inventory Endpoints:
- POST /api/packages/{package_id}/confirm (Endpoint 14)
- GET /api/reservations/{ref} (Endpoint 15)
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


def test_confirm_reservation_success(client: TestClient, mock_engine):
    """Confirming a package generates 10-digit reference and marks package BOOKED."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    confirm_payload = {
        "customer_name": "Rohan Menon",
        "customer_email": "rohan.menon@example.com",
        "customer_phone": "+91 9876543210",
    }
    confirm_res = client.post(f"/api/packages/{pkg_id}/confirm", json=confirm_payload)
    assert confirm_res.status_code == 201
    data = confirm_res.json()

    # Verify exact 10-digit numeric reference (PRD Section 10)
    ref = data["reservation_reference"]
    assert len(ref) == 10
    assert ref.isdigit()
    assert data["status"] == "CONFIRMED"
    assert data["customer_name"] == "Rohan Menon"
    assert data["customer_email"] == "rohan.menon@example.com"
    assert len(data["items"]) > 0

    # Verify package status is now BOOKED
    pkg_res = client.get(f"/api/packages/{pkg_id}")
    assert pkg_res.json()["status"] == "BOOKED"


def test_double_booking_prevention(client: TestClient, mock_engine):
    """Attempting to confirm an already booked package must fail with 409 Conflict."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    payload = {"customer_name": "Rohan Menon", "customer_email": "rohan@example.com"}
    res1 = client.post(f"/api/packages/{pkg_id}/confirm", json=payload)
    assert res1.status_code == 201

    res2 = client.post(f"/api/packages/{pkg_id}/confirm", json=payload)
    assert res2.status_code == 409
    assert res2.json()["code"] in ("CONFLICT", "ALREADY_BOOKED")


def test_get_reservation_by_reference(client: TestClient, mock_engine):
    """GET /api/reservations/{ref} retrieves confirmed booking details."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    payload = {"customer_name": "Rohan Menon", "customer_email": "rohan@example.com"}
    confirm_res = client.post(f"/api/packages/{pkg_id}/confirm", json=payload)
    ref = confirm_res.json()["reservation_reference"]

    get_res = client.get(f"/api/reservations/{ref}")
    assert get_res.status_code == 200
    res_data = get_res.json()
    assert res_data["reservation_reference"] == ref
    assert res_data["package_id"] == pkg_id
    assert res_data["status"] == "CONFIRMED"
    assert res_data["customer_name"] == "Rohan Menon"


def test_get_nonexistent_reservation_returns_404(client: TestClient):
    """GET /api/reservations/{ref} with unknown 10-digit reference returns 404."""
    res = client.get("/api/reservations/9999999999")
    assert res.status_code == 404
    assert res.json()["code"] == "NOT_FOUND"


def test_get_invalid_reference_format_returns_400(client: TestClient):
    """GET /api/reservations/{ref} with non-10-digit format returns 400."""
    res = client.get("/api/reservations/INVALIDREF")
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_REFERENCE"

"""Confirm + lookup on the REAL engine (M7, S2):
POST /api/packages/{id}/confirm (14) · GET /api/reservations/{ref} (15)
"""

from tests.api.test_packages_api import build


def confirm(client, pkg_id, **body):
    return client.post(f"/api/packages/{pkg_id}/confirm", json=body)


def test_confirm_gives_10_digit_reference_and_books_the_package(client):
    pkg_id = build(client).json()["package_id"]
    r = confirm(client, pkg_id, customer_name="Rohan Menon", customer_email="rohan@example.com")
    assert r.status_code == 201
    d = r.json()
    ref = d["reference"]
    assert len(ref) == 10 and ref.isdigit() and ref[0] != "0"
    assert d["status"] == "CONFIRMED" and d["total_inr"] == 230440
    assert all(i["status"] == "BOOKED" and i["booking"] == {"reference": ref} for i in d["items"])
    assert client.get(f"/api/packages/{pkg_id}").json()["status"] == "BOOKED"


def test_double_confirm_returns_the_same_reference(client):
    pkg_id = build(client).json()["package_id"]
    first = confirm(client, pkg_id).json()["reference"]
    again = confirm(client, pkg_id)
    assert again.status_code == 201 and again.json()["reference"] == first


def test_lookup_by_reference(client):
    pkg_id = build(client).json()["package_id"]
    ref = confirm(client, pkg_id, customer_name="Rohan Menon").json()["reference"]
    d = client.get(f"/api/reservations/{ref}").json()
    assert d["reference"] == ref and d["package_id"] == pkg_id and d["status"] == "CONFIRMED"
    assert d["customer_name"] == "Rohan Menon" and d["snapshot"]["items"][0]["booking"]["reference"] == ref


def test_unknown_reference_is_404_reservation_not_found(client):
    r = client.get("/api/reservations/9999999999")
    assert r.status_code == 404 and r.json()["message"] == "Reservation not found"


def test_bad_reference_format_is_400(client):
    for bad in ("12345", "abcdefghij"):
        r = client.get(f"/api/reservations/{bad}")
        assert r.status_code == 400 and r.json()["code"] == "INVALID_REFERENCE"


def test_stale_base_version_on_confirm_is_409(client):
    pkg_id = build(client).json()["package_id"]
    r = confirm(client, pkg_id, base_version=4)
    assert r.status_code == 409 and r.json()["code"] == "VERSION_CONFLICT"


def test_bookings_use_up_seats_and_rooms(client):
    """S2: identical bookings eventually run out of seats or rooms and are refused with SOLD_OUT."""
    codes = []
    for _ in range(6):
        pkg_id = build(client).json()["package_id"]
        r = confirm(client, pkg_id)
        codes.append(r.status_code if r.status_code == 201 else r.json()["code"])
        if r.status_code != 201:
            break
    assert codes[0] == 201 and codes[-1] == "SOLD_OUT"

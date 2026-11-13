"""Endpoint 13: GET /api/packages/{id}/export, shared trip format (DATA_DICTIONARY section 4)."""

import json

from app.core.config import get_settings
from tests.api.test_packages_api import build


def test_export_is_a_trip_format_attachment(client):
    pkg_id = build(client).json()["package_id"]
    r = client.get(f"/api/packages/{pkg_id}/export")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert "attachment" in r.headers["content-disposition"] and f"trip-{pkg_id}.json" in r.headers["content-disposition"]

    data = r.json()
    example = json.loads((get_settings().DATA_DIR / "trip_format_example.json").read_text(encoding="utf-8"))
    assert set(example) <= set(data) | {"country"} and data["country"] == "Japan"
    assert set(example["items"][0]) <= set(data["items"][0])
    assert data["total_inr"] == sum(i["price_inr"] for i in data["items"]) == 230440
    hotel = next(i for i in data["items"] if i["type"] == "hotel")
    assert hotel["room_id"] and len(hotel["start"]) == 10
    flight = next(i for i in data["items"] if i["type"] == "flight")
    assert len(flight["start"]) == 16 and all(i["sources"] == [] for i in data["items"])


def test_export_after_confirm_is_booked_with_reference(client):
    pkg_id = build(client).json()["package_id"]
    ref = client.post(f"/api/packages/{pkg_id}/confirm", json={}).json()["reference"]
    items = client.get(f"/api/packages/{pkg_id}/export").json()["items"]
    assert all(i["status"] == "BOOKED" and i["booking"] == {"reference": ref} for i in items)


def test_export_unknown_package_is_404(client):
    assert client.get("/api/packages/pkg-nope/export").status_code == 404

"""Change endpoints on the REAL engine (M6, G1, G2):
GET .../options/hotel (6) · .../options/flight (7) · .../options/attraction (8) · PATCH /api/packages/{id} (9)
"""

import pytest

from tests.api.test_packages_api import build


@pytest.fixture
def pkg(client):
    return build(client).json()       # Menon: Tokyo 2 + Osaka 4


def patch(client, pkg_id, change, base_version=None):
    body = {"change": change}
    if base_version is not None:
        body["base_version"] = base_version
    return client.patch(f"/api/packages/{pkg_id}", json=body)


# ---------------------------------------------------------------- options
def test_hotel_options_have_price_diff(client, pkg):
    r = client.get(f"/api/packages/{pkg['package_id']}/options/hotel", params={"city": "Osaka"})
    assert r.status_code == 200
    opts = r.json()["options"]
    assert len(opts) > 1 and all({"catalog_id", "room_id", "price_diff"} <= set(o) for o in opts)
    assert [o["price_diff"] for o in opts if o["details"]["current"]] == [0]


def test_flight_options(client, pkg):
    opts = client.get(f"/api/packages/{pkg['package_id']}/options/flight", params={"leg": "arrival"}).json()["options"]
    assert {"FL-401", "FL-405"} <= {o["catalog_id"] for o in opts}


def test_attraction_options_need_a_date(client, pkg):
    ok = client.get(f"/api/packages/{pkg['package_id']}/options/attraction", params={"date": "2027-04-13"})
    assert ok.status_code == 200 and ok.json()["options"]
    missing = client.get(f"/api/packages/{pkg['package_id']}/options/attraction")
    assert missing.status_code == 422 and missing.json()["code"] == "INVALID_OPTION_QUERY"


# ---------------------------------------------------------------- PATCH
def test_change_hotel_creates_new_version_with_new_total(client, pkg):
    pkg_id = pkg["package_id"]
    opt = next(o for o in client.get(f"/api/packages/{pkg_id}/options/hotel", params={"city": "Osaka"})
               .json()["options"] if not o["details"]["current"])
    r = patch(client, pkg_id, {"type": "hotel", "city": "Osaka", "hotel_id": opt["catalog_id"],
                               "room_id": opt["room_id"]}, base_version=1)
    assert r.status_code == 200
    d = r.json()
    assert d["version"] == 2 and d["total_inr"] == pkg["total_inr"] + opt["price_diff"]
    assert any(i["catalog_id"] == opt["catalog_id"] for i in d["items"])


def test_later_arrival_flight_retimes_transfer(client, pkg):
    r = patch(client, pkg["package_id"], {"type": "flight", "leg": "arrival", "flight_id": "FL-405"})
    assert r.status_code == 200
    assert any("Arrival transfer" in s for s in r.json()["side_effects"])


def test_add_and_remove_attraction(client, pkg):
    pkg_id = pkg["package_id"]
    opt = client.get(f"/api/packages/{pkg_id}/options/attraction", params={"date": "2027-04-13"}).json()["options"][0]
    added = patch(client, pkg_id, {"type": "add_attraction", "date": "2027-04-13", "attraction_id": opt["catalog_id"],
                                   "start": opt["start"]})
    assert added.status_code == 200
    item = next(i for i in added.json()["items"] if i["catalog_id"] == opt["catalog_id"])
    removed = patch(client, pkg_id, {"type": "remove_attraction", "item_id": item["item_id"]})
    assert removed.status_code == 200 and removed.json()["version"] == 3


def test_change_breaking_a_rule_is_refused_and_package_unchanged(client, pkg):
    pkg_id = pkg["package_id"]
    r = patch(client, pkg_id, {"type": "add_attraction", "date": "2027-04-13", "attraction_id": "ATT-OSA-003",
                               "start": "2027-04-13T03:00"})
    assert r.status_code == 409 and r.json()["code"] == "RULE_VIOLATION"
    assert {v["rule_id"] for v in r.json()["details"]["violations"]} >= {"A1"}
    assert client.get(f"/api/packages/{pkg_id}").json()["version"] == 1


def test_impossible_change_is_422(client, pkg):
    r = patch(client, pkg["package_id"], {"type": "remove_attraction", "item_id": "i1"})   # i1 is a flight
    assert r.status_code == 422 and r.json()["code"] == "INVALID_CHANGE"


def test_stale_base_version_is_409(client, pkg):
    r = patch(client, pkg["package_id"], {"type": "flight", "leg": "arrival", "flight_id": "FL-405"}, base_version=5)
    assert r.status_code == 409 and r.json()["code"] == "VERSION_CONFLICT"


def test_booked_package_cannot_change(client, pkg):
    pkg_id = pkg["package_id"]
    assert client.post(f"/api/packages/{pkg_id}/confirm", json={}).status_code == 201
    r = patch(client, pkg_id, {"type": "flight", "leg": "arrival", "flight_id": "FL-405"})
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_BOOKED"


def test_later_flight_home_warns_about_check_out(client):
    """G1: a return flight that makes you leave the hotel after check-out gives a warning."""
    pkg = build(client, country="United Arab Emirates", start_date="2027-04-13", nights=5, children_ages=[],
                budget_inr=900000).json()
    r = patch(client, pkg["package_id"], {"type": "flight", "leg": "return", "flight_id": "FL-1320"})
    assert r.status_code == 200
    assert any("check-out" in w for w in r.json()["warnings"])

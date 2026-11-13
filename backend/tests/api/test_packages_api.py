"""Package lifecycle endpoints on the REAL engine:
POST /api/packages (4) · GET /api/packages/{id} (5) · GET .../city-plans (10) · POST .../rebuild (11) · POST .../undo (12)
"""

from decimal import Decimal

import pytest

MENON = {"departure_city": "Bengaluru", "country": "Japan", "start_date": "2027-04-10", "nights": 6,
         "adults": 2, "children_ages": [6], "budget_inr": 350000, "traveler_name": "Menon family"}


def build(client, **overrides):
    return client.post("/api/packages", json={**MENON, **overrides})


# ---------------------------------------------------------------- build (M1, M2, M5, M8, G4)
def test_build_menon_package(client):
    r = build(client)
    assert r.status_code == 201
    d = r.json()
    assert d["outcome"] == "PACKAGE" and d["status"] == "PLANNED" and d["version"] == 1
    assert d["total_inr"] == 230440 == sum(i["price_inr"] for i in d["items"])
    assert d["totals"]["left_inr"] == 350000 - 230440 and d["totals"]["over_budget"] is False
    assert [c["city"] for c in d["package"]["city_plan"]] == ["Tokyo", "Osaka"]
    assert d["package"]["traveler"]["name"] == "Menon family"


def test_timeline_has_every_day_and_the_overnight_arrival_flight(client):
    d = build(client).json()
    days = d["timeline"]
    assert len(days) == 7 and days[0]["date"] == "2027-04-10"
    assert days[0]["events"][0]["type"] == "flight"          # departs 9 Apr 23:50, shown on day 1
    assert days[-1]["events"][-1]["type"] == "flight"        # return flight on the last day
    assert sum(len(day["events"]) for day in days) == len(d["items"])


def test_airport_code_and_uae_alias_are_accepted(client):
    r = build(client, departure_city="BOM", country="UAE", start_date="2027-04-05", nights=5, children_ages=[])
    assert r.status_code == 201 and r.json()["package"]["country"] == "United Arab Emirates"


def test_mode_three_returns_g4_alternatives(client):
    d = build(client, mode="three").json()
    assert set(d["alternatives"]) == {"cheapest", "fastest", "best_rated"}


def test_over_budget_returns_cheapest_and_suggestion(client):
    r = build(client, budget_inr=50000)
    assert r.status_code == 200
    d = r.json()
    assert d["outcome"] == "OVER_BUDGET" and d["cheapest_total"] == 219324
    assert d["over_by"] == 219324 - 50000 and d["suggestion"]
    assert client.get(f"/api/packages/{d['package_id']}").status_code == 200    # the cheapest can be viewed


def test_no_package_returns_reason(client):
    # every MAA return flight that day has fewer than 8 seats left
    r = build(client, departure_city="Chennai", country="United Arab Emirates", start_date="2027-04-08", nights=4,
              adults=4, children_ages=[3, 5, 8, 12], budget_inr=600000)
    assert r.status_code == 200 and r.json()["outcome"] == "NO_PACKAGE" and r.json()["reason"]


@pytest.mark.parametrize("override,field", [
    ({"budget_inr": -1000}, "budget"),
    ({"adults": 0}, "adults"),
    ({"nights": 11}, "nights"),
    ({"start_date": "2027-03-20"}, "start_date"),
    ({"start_date": "2027-04-18", "nights": 3}, "request"),       # returns 21 Apr, after the window
    ({"children_ages": [18]}, "request"),
    ({"adults": 6, "children_ages": [1, 2, 3, 4]}, "request"),     # 10 travelers
])
def test_invalid_input_gives_422_with_field_errors(client, override, field):
    r = build(client, **override)
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "INVALID_INPUT" and field in body["details"]["field_errors"]


# ---------------------------------------------------------------- get, city plans, rebuild, undo
def test_get_package_and_404(client):
    pkg_id = build(client).json()["package_id"]
    d = client.get(f"/api/packages/{pkg_id}").json()
    assert d["package_id"] == pkg_id and d["version"] == 1 and d["timeline"]
    r = client.get("/api/packages/pkg-does-not-exist")
    assert r.status_code == 404 and r.json()["code"] == "NOT_FOUND"


def test_city_plans_are_ranked(client):
    pkg_id = build(client).json()["package_id"]
    plans = client.get(f"/api/packages/{pkg_id}/city-plans").json()["city_plans"]
    assert len(plans) == 27 and all({"cities", "nights", "total_inr", "valid"} <= set(p) for p in plans)
    totals = [p["total_inr"] for p in plans if p["valid"]]
    assert totals == sorted(totals)


def test_rebuild_on_another_plan_then_undo(client):
    pkg_id = build(client).json()["package_id"]
    plans = client.get(f"/api/packages/{pkg_id}/city-plans").json()["city_plans"]
    three = next(p for p in plans if len(p["cities"]) == 3 and p["valid"])

    r = client.post(f"/api/packages/{pkg_id}/rebuild", json={"city_plan": three, "base_version": 1})
    assert r.status_code == 200 and r.json()["version"] == 2
    assert [c["city"] for c in r.json()["package"]["city_plan"]] == three["cities"]

    undo = client.post(f"/api/packages/{pkg_id}/undo")
    assert undo.status_code == 200 and undo.json()["version"] == 3
    assert undo.json()["package"]["total_inr"] == 230440


def test_rebuild_rejects_invalid_plan_and_stale_version(client):
    pkg_id = build(client).json()["package_id"]
    bad = client.post(f"/api/packages/{pkg_id}/rebuild", json={"city_plan": [{"city": "Tokyo", "nights": 1}]})
    assert bad.status_code == 409 and bad.json()["code"] == "INVALID_CITY_PLAN"
    stale = client.post(f"/api/packages/{pkg_id}/rebuild",
                        json={"city_plan": {"cities": ["Tokyo"], "nights": [6]}, "base_version": 7})
    assert stale.status_code == 409 and stale.json()["code"] == "VERSION_CONFLICT"


def test_undo_on_version_1_is_refused(client):
    pkg_id = build(client).json()["package_id"]
    r = client.post(f"/api/packages/{pkg_id}/undo")
    assert r.status_code == 409 and r.json()["code"] == "CANNOT_UNDO"


# ---------------------------------------------------------------- persistence (repositories)
def test_persistence_across_separate_sessions(db_session):
    from app.packages.repository import PackageRepository
    from app.reservations.repository import ReservationRepository
    from tests.conftest import TestingSessionLocal

    s1 = TestingSessionLocal()
    PackageRepository(s1).create_package(package_id="pkg-persist", total_price=Decimal("50000"),
                                         initial_data={"items": [{"item_id": "i1", "type": "hotel"}]})
    s1.commit()
    s1.close()

    s2 = TestingSessionLocal()
    repo2 = PackageRepository(s2)
    assert repo2.get_package("pkg-persist").current_version_no == 1
    repo2.save_version("pkg-persist", {"items": []}, "Swapped hotel", Decimal("52000"))
    s2.commit()
    s2.close()

    s3 = TestingSessionLocal()
    pkg = PackageRepository(s3).get_package("pkg-persist")
    assert pkg.current_version_no == 2 and len(pkg.versions) == 2
    res = ReservationRepository(s3).create_reservation("pkg-persist", pkg.total_price, pkg.current_version.snapshot)
    s3.commit()
    ref = res.reference
    s3.close()

    s4 = TestingSessionLocal()
    loaded = ReservationRepository(s4).get_by_reference(ref)
    assert loaded is not None and loaded.package_id == "pkg-persist" and len(ref) == 10
    s4.close()


def test_failed_transaction_leaves_nothing(db_session):
    from app.models import Package
    from tests.conftest import TestingSessionLocal

    s = TestingSessionLocal()
    try:
        s.add(Package(package_id="pkg-rollback", status="PLANNED", total_price=Decimal("1")))
        s.flush()
        s.add(Package(package_id="pkg-rollback", status="PLANNED", total_price=Decimal("1")))
        s.flush()
    except Exception:
        s.rollback()
    finally:
        s.close()
    verify = TestingSessionLocal()
    assert verify.get(Package, "pkg-rollback") is None
    verify.close()


def test_view_items_carry_catalog_details_and_days_have_a_city(client):
    """The UI shows real airline / hotel / image data; the stored package stays in the shared trip format."""
    d = build(client).json()
    items = {i["item_id"]: i for i in d["items"]}
    assert items["i1"]["details"]["leg"] == "arrival" and items["i1"]["details"]["airline"]
    assert items["i11"]["details"]["leg"] == "return"
    hotel = next(i for i in d["items"] if i["type"] == "hotel")
    assert hotel["details"]["hotel_name"] and hotel["details"]["room_name"] and hotel["details"]["nights"] == 2
    assert all("details" not in i for i in d["package"]["items"])
    assert [day["city"] for day in d["timeline"]] == ["Tokyo", "Tokyo"] + ["Osaka"] * 5

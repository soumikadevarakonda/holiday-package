"""Every fixture request gives its expected outcome, and every returned package passes validate()."""

import json
from datetime import date
from pathlib import Path

import pytest

from app.builder.search import build, rebuild
from app.core.package_model import TripRequest
from app.rules.validator import validate

FIXTURES = json.loads((Path(__file__).parents[1] / "fixtures" / "requests.json").read_text(encoding="utf-8"))


def to_request(d: dict) -> TripRequest:
    return TripRequest(d["departure_city"], d["country"], date.fromisoformat(d["start_date"]), d["nights"],
                       d["adults"], tuple(d["children_ages"]), d["budget_inr"], d.get("traveler_name", "Traveler"))


@pytest.mark.parametrize("case", FIXTURES, ids=[c["id"] for c in FIXTURES])
def test_fixture_outcomes(case, catalog_store):
    res = build(to_request(case["request"]), mode="three")
    exp = case["expect"]
    assert res.outcome == exp["outcome"], res.reason
    if res.package:
        assert validate(res.package, initial=True) == []
        for alt in res.alternatives.values():
            assert validate(alt, initial=True) == []
    if "cities" in exp:
        assert len(res.package.city_plan) == exp["cities"]
    if "first_city" in exp:
        assert res.package.city_plan[0].city == exp["first_city"]
    if "plans" in exp:
        assert len(res.city_plans) == exp["plans"]
    if "rooms_per_hotel" in exp:
        assert all(i.quantity == exp["rooms_per_hotel"] for i in res.package.items if i.type == "hotel")
    if "reason_contains" in exp:
        assert exp["reason_contains"] in res.reason


def test_menon_fits_budget_and_is_deterministic(catalog_store):
    req = to_request(FIXTURES[0]["request"])
    a, b = build(req), build(req)
    assert a.package.total_inr <= req.budget_inr
    assert a.package.to_trip_format() == b.package.to_trip_format()


def test_over_budget_reports_cheapest_and_suggestion(catalog_store):
    res = build(to_request(next(c for c in FIXTURES if c["id"] == "tiny_budget")["request"]))
    assert res.cheapest_total == res.package.total_inr
    assert res.over_by == res.cheapest_total - 50000 > 0
    assert res.suggestion


def test_rebuild_on_another_plan(catalog_store):
    req = to_request(FIXTURES[0]["request"])
    other = next(s for s in build(req).city_plans if len(s.plan) == 3 and s.valid)
    res = rebuild(req, other.plan)
    assert res.outcome == "PACKAGE" and [c.city for c in res.package.city_plan] == [c.city for c in other.plan]
    assert validate(res.package) == []


def test_rebuild_refuses_invalid_plan(catalog_store):
    from app.core.package_model import CityStay
    res = rebuild(to_request(FIXTURES[0]["request"]), [CityStay("Tokyo", 1), CityStay("Kyoto", 5)])
    assert res.outcome == "NO_PACKAGE"

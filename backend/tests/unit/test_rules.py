"""One pass case and one fail case per rule ID, starting from the valid Menon fixture.

Fixture items: i1 FL-401 · i2 NRT bus (pickup 11:30) · i3 Tokyo hotel 10→13 Apr · i4, i5 Tokyo attractions ·
i6 train Tokyo→Kyoto 13 Apr 10:00 · i7 Kyoto hotel 13→16 Apr · i8, i9 Kyoto attractions ·
i10 Kyoto→KIX bus · i11 FL-411.
"""

import pytest

from app.core.package_model import CityStay
from app.rules.validator import validate
from tests.helpers import menon_package


@pytest.fixture
def pkg(catalog_store):
    return menon_package()


def item(p, item_id):
    return next(i for i in p.items if i.item_id == item_id)


def rule_ids(p, **kw) -> set[str]:
    return {v.rule_id for v in validate(p, **kw)}


def test_menon_fixture_passes_every_rule(pkg):
    assert validate(pkg, initial=True) == []


# ---------------------------------------------------------------- D
def test_d1_first_night_before_window(pkg):
    pkg.start_date = "2027-03-31"
    assert "D1" in rule_ids(pkg)


def test_d2_city_not_in_country(pkg):
    pkg.country = "United Arab Emirates"
    assert "D2" in rule_ids(pkg)


def test_d3_plan_does_not_match_hotels(pkg):
    pkg.city_plan = [CityStay("Tokyo", 4), CityStay("Kyoto", 2)]
    assert "D3" in rule_ids(pkg)


# ---------------------------------------------------------------- F
def test_f1_missing_return_flight(pkg):
    pkg.items = [i for i in pkg.items if i.item_id != "i11"]
    assert "F1" in rule_ids(pkg)


def test_f2_arrival_airport_does_not_serve_first_city(pkg):
    item(pkg, "i1").catalog_id = "FL-740"      # BLR -> KIX lands 10 Apr, KIX does not serve Tokyo
    assert "F2" in rule_ids(pkg)


def test_f3_return_airport_does_not_serve_last_city(pkg):
    item(pkg, "i11").catalog_id = "FL-412"     # HND -> BLR, HND does not serve Kyoto
    assert "F3" in rule_ids(pkg)


def test_f4_not_enough_seats(pkg):
    assert "F4" not in rule_ids(pkg)
    assert "F4" in rule_ids(pkg, seats_used={"FL-401": 8})   # S2: 9 left - 8 booked < 3 travelers


# ---------------------------------------------------------------- AT
def test_at1_missing_return_transfer(pkg):
    pkg.items = [i for i in pkg.items if i.item_id != "i10"]
    assert "AT1" in rule_ids(pkg)


def test_at2_pickup_too_soon_after_landing(pkg):
    item(pkg, "i2").start = "2027-04-10T11:00"    # landing 10:30
    assert "AT2" in rule_ids(pkg)


def test_at3_reaches_airport_too_late(pkg):
    item(pkg, "i10").start = "2027-04-16T08:00"   # 100-min bus -> 09:40, flight 12:00
    assert "AT3" in rule_ids(pkg)


def test_at4_outside_service_hours(pkg, catalog_store):
    bus = catalog_store.get_transfer(item(pkg, "i10").catalog_id)
    h, m = map(int, bus.service_from.split(":"))
    item(pkg, "i10").start = f"2027-04-16T{(h * 60 + m - 1) // 60:02d}:{(h * 60 + m - 1) % 60:02d}"
    assert "AT4" in rule_ids(pkg)


# ---------------------------------------------------------------- CT
def test_ct1_train_off_the_30_minute_grid(pkg):
    item(pkg, "i6").start = "2027-04-13T10:10"
    assert "CT1" in rule_ids(pkg)


def test_ct1_missing_intercity_transfer(pkg):
    pkg.items = [i for i in pkg.items if i.item_id != "i6"]
    assert "CT1" in rule_ids(pkg)


# ---------------------------------------------------------------- H
def test_h1_night_without_hotel(pkg):
    item(pkg, "i7").end = "2027-04-15"
    assert "H1" in rule_ids(pkg)


def test_h2_room_of_another_hotel(pkg):
    item(pkg, "i7").room_id = "RM-TYO-001-A"
    assert "H2" in rule_ids(pkg)


def test_h3_more_rooms_than_adults(pkg):
    item(pkg, "i3").quantity = 3                  # 2 adults cannot fill 3 rooms (adults >= k)
    assert "H3" in rule_ids(pkg)


def test_h4_no_rooms_left(pkg):
    assert "H4" in rule_ids(pkg, rooms_used={("RM-TYO-004-B", "2027-04-11"): 99})


# ---------------------------------------------------------------- A
def test_a1_visit_before_opening(pkg):
    item(pkg, "i4").start = "2027-04-11T05:00"
    assert "A1" in rule_ids(pkg)


def test_a1_attraction_in_another_city(pkg):
    item(pkg, "i4").catalog_id = "ATT-KYO-001"    # Kyoto attraction on a Tokyo night
    assert "A1" in rule_ids(pkg)


def test_a2_same_attraction_twice(pkg):
    item(pkg, "i5").catalog_id = item(pkg, "i4").catalog_id
    assert "A2" in rule_ids(pkg)


def test_a3_full_day_without_attraction_only_for_initial_package(pkg):
    pkg.items = [i for i in pkg.items if i.item_id != "i4"]
    assert "A3" in rule_ids(pkg, initial=True)
    assert "A3" not in rule_ids(pkg)              # after a change, removal is allowed (M6)


def test_a4_attraction_on_return_day(pkg):
    item(pkg, "i9").start = "2027-04-16T09:30"
    assert "A4" in rule_ids(pkg)


# ---------------------------------------------------------------- P
def test_p1_wrong_price(pkg):
    item(pkg, "i1").price_inr = 1
    assert "P1" in rule_ids(pkg)


def test_p1_within_one_percent_is_accepted(pkg):
    it = item(pkg, "i1")
    it.price_inr = int(it.price_inr * 1.005)
    assert "P1" not in rule_ids(pkg)

"""M6 / G1 / G2: change options and apply_change on a built Menon package (Tokyo 2 + Osaka 4)."""

import pytest

from app.builder.search import build
from app.changes.options import options
from app.changes.side_effects import ChangeError, apply_change
from app.core.package_model import Change
from app.rules.validator import validate
from tests.helpers import MENON_REQUEST


@pytest.fixture
def pkg(catalog_store):
    return build(MENON_REQUEST).package


def first(pkg, kind):
    return next(i for i in pkg.items if i.type == kind)


# ---------------------------------------------------------------- options (M6, G2)
@pytest.mark.parametrize("kind,params", [("hotel", {"city": "Osaka"}), ("hotel", {"city": "Tokyo"}),
                                         ("flight", {"leg": "arrival"}), ("flight", {"leg": "return"}),
                                         ("attraction", {"date": "2027-04-13"})])
def test_every_option_keeps_the_package_valid(pkg, kind, params):
    opts = options(pkg, kind, **params)
    assert opts
    for o in opts:
        if o.details.get("current"):
            assert o.price_diff == 0
            continue
        if kind == "hotel":
            ch = Change(type="hotel", city=params["city"], hotel_id=o.catalog_id, room_id=o.room_id)
        elif kind == "flight":
            ch = Change(type="flight", leg=params["leg"], flight_id=o.catalog_id)
        else:
            ch = Change(type="add_attraction", date=params["date"], attraction_id=o.catalog_id, start=o.start)
        new = apply_change(pkg, ch).package
        assert validate(new) == []
        assert new.total_inr - pkg.total_inr == o.price_diff      # G2 is the true total difference


def test_hotel_options_include_the_current_choice_once(pkg):
    current = [o for o in options(pkg, "hotel", city="Osaka") if o.details["current"]]
    assert len(current) == 1 and current[0].price_diff == 0


def test_attraction_options_exclude_ones_already_in_the_package(pkg):
    in_pkg = {i.catalog_id for i in pkg.items if i.type == "attraction"}
    assert not in_pkg & {o.catalog_id for o in options(pkg, "attraction", date="2027-04-14")}


def test_arrival_day_attractions_start_after_reaching_the_city(pkg):
    reach = first(pkg, "transfer").end
    assert all(o.start >= reach for o in options(pkg, "attraction", date=pkg.start_date))


# ---------------------------------------------------------------- apply_change (M6, G1)
def test_later_arrival_flight_retimes_the_transfer(pkg):
    later = max((o for o in options(pkg, "flight", leg="arrival") if not o.details["current"]),
                key=lambda o: o.details["arrival_local"])
    res = apply_change(pkg, Change(type="flight", leg="arrival", flight_id=later.catalog_id))
    assert validate(res.package) == []
    assert any("Arrival transfer" in s for s in res.side_effects)


def test_later_arrival_drops_arrival_day_visit_that_no_longer_fits(pkg):
    early = apply_change(pkg, Change(type="add_attraction", date=pkg.start_date,
                                     attraction_id=options(pkg, "attraction", date=pkg.start_date)[0].catalog_id))
    later = max((o for o in options(early.package, "flight", leg="arrival") if not o.details["current"]),
                key=lambda o: o.details["arrival_local"])
    res = apply_change(early.package, Change(type="flight", leg="arrival", flight_id=later.catalog_id))
    assert any(s.startswith("Removed") for s in res.side_effects)
    assert validate(res.package) == []


def test_hotel_change_in_first_city_updates_the_airport_transfer(pkg):
    alt = next(o for o in options(pkg, "hotel", city="Tokyo") if o.details["area"] != "Ginza")
    res = apply_change(pkg, Change(type="hotel", city="Tokyo", hotel_id=alt.catalog_id, room_id=alt.room_id))
    assert validate(res.package) == []
    hotel = next(i for i in res.package.items if i.type == "hotel" and i.city == "Tokyo")
    assert hotel.catalog_id == alt.catalog_id


def test_add_attraction_at_a_closed_time_is_caught_by_validate(pkg):
    res = apply_change(pkg, Change(type="add_attraction", date="2027-04-13", attraction_id="ATT-OSA-003",
                                   start="2027-04-13T03:00"))
    assert {v.rule_id for v in validate(res.package)} >= {"A1"}


def test_remove_attraction_warns_when_a_day_is_left_empty(pkg):
    att = first(pkg, "attraction")
    res = apply_change(pkg, Change(type="remove_attraction", item_id=att.item_id))
    assert att.item_id not in {i.item_id for i in res.package.items}
    assert res.warnings and validate(res.package) == []          # A3 only applies to the first package


def test_apply_change_never_modifies_the_input(pkg):
    before = pkg.to_trip_format()
    apply_change(pkg, Change(type="remove_attraction", item_id=first(pkg, "attraction").item_id))
    assert pkg.to_trip_format() == before


@pytest.mark.parametrize("change", [
    Change(type="hotel", city="Kyoto", hotel_id="HTL-KYO-001", room_id="RM-KYO-001-A"),   # no Kyoto stay
    Change(type="hotel", city="Osaka", hotel_id="HTL-TYO-001", room_id="RM-TYO-001-A"),   # wrong city
    Change(type="flight", leg="arrival", flight_id="FL-NOPE"),
    Change(type="remove_attraction", item_id="i1"),                                        # a flight
    Change(type="add_attraction", date="2027-04-13", attraction_id="ATT-NOPE"),
])
def test_impossible_changes_raise_change_error(pkg, change):
    with pytest.raises(ChangeError):
        apply_change(pkg, change)

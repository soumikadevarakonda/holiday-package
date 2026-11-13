"""Valid alternatives for a package part, each with price_diff (M6, G2).  (Person A)

Every option is applied to a copy and checked with validate(), so the traveler only sees choices that keep
the whole package valid (T5). price_diff = new package total - current total, so knock-on price changes
(e.g. a taxi instead of a bus after a later flight) are included.
"""

from __future__ import annotations

from datetime import date

from app.builder.flights import arrival_flights, return_flights
from app.builder.hotels import stay_options
from app.catalog.store import get_store
from app.changes.side_effects import (
    ChangeError,
    apply_change,
    city_of_night,
    find_slot,
    flight_items,
    hotel_items,
    items_of,
    travelers,
)
from app.core.package_model import Change, Option, OptionKind, Package
from app.core.timeutil import format_iso_hm
from app.pricing.calculator import calculate_attraction_price
from app.rules.validator import validate


def _try(pkg: Package, change: Change):
    try:
        res = apply_change(pkg, change)
    except ChangeError:
        return None
    return None if validate(res.package) else res


def options(pkg: Package, kind: OptionKind, **params) -> list[Option]:
    """kind="hotel" (city=…), "flight" (leg="arrival"|"return"), "attraction" (date="YYYY-MM-DD")."""
    if kind == "hotel":
        return _hotel_options(pkg, params["city"])
    if kind == "flight":
        return _flight_options(pkg, params["leg"])
    if kind == "attraction":
        return _attraction_options(pkg, date.fromisoformat(params["date"]))
    raise ChangeError(f"Unknown option kind '{kind}'.")


def _hotel_options(pkg: Package, city: str) -> list[Option]:
    item = next((h for h in hotel_items(pkg) if h.city == city), None)
    if item is None:
        raise ChangeError(f"The package has no hotel in {city}.")
    adults, children = travelers(pkg)
    check_in, check_out = date.fromisoformat(item.start), date.fromisoformat(item.end)
    out = []
    for o in stay_options(city, check_in, (check_out - check_in).days, adults, children):
        current = (o.hotel.hotel_id, o.room.room_id) == (item.catalog_id, item.room_id)
        res = None if current else _try(pkg, Change(type="hotel", city=city, hotel_id=o.hotel.hotel_id,
                                                    room_id=o.room.room_id))
        if not current and res is None:
            continue
        out.append(Option(
            kind="hotel", catalog_id=o.hotel.hotel_id, room_id=o.room.room_id,
            label=f"{o.hotel.name} · {o.rooms} × {o.room.name}", price_inr=o.price,
            price_diff=0 if current else res.package.total_inr - pkg.total_inr,
            details={"current": current, "stars": o.hotel.stars, "rating": o.hotel.rating, "area": o.hotel.area,
                     "rooms": o.rooms, "room_type": o.room.room_type, "room_name": o.room.name,
                     "refundable": o.room.refundable, "image": o.hotel.image,
                     "side_effects": [] if current else res.side_effects}))
    return sorted(out, key=lambda x: (x.price_diff, x.catalog_id, x.room_id))


def _flight_options(pkg: Package, leg: str) -> list[Option]:
    if leg not in ("arrival", "return"):
        raise ChangeError("leg must be 'arrival' or 'return'.")
    store = get_store()
    adults, children = travelers(pkg)
    arr_item, ret_item = flight_items(pkg)
    current_id = (arr_item if leg == "arrival" else ret_item).catalog_id
    cities = set(store.get_country(pkg.country).cities)
    home = pkg.traveler.home_airport
    if leg == "arrival":
        flights = arrival_flights(home, cities, date.fromisoformat(pkg.start_date), adults + children)
    else:
        flights = return_flights(home, cities, date.fromisoformat(pkg.end_date), adults + children)
    out = []
    for f in flights:
        current = f.flight_id == current_id
        res = None if current else _try(pkg, Change(type="flight", leg=leg, flight_id=f.flight_id))
        if not current and res is None:
            continue
        out.append(Option(
            kind="flight", catalog_id=f.flight_id, label=f"{f.flight_number} {f.from_airport} → {f.to_airport}",
            price_inr=f.price_per_seat * (adults + children),
            price_diff=0 if current else res.package.total_inr - pkg.total_inr,
            details={"current": current, "airline": f.airline, "departure_local": f.departure_local[:16],
                     "arrival_local": f.arrival_local[:16], "duration_minutes": f.duration_minutes,
                     "stops": f.stops, "seats_left": f.seats_left,
                     "side_effects": [] if current else res.side_effects,
                     "warnings": [] if current else res.warnings}))
    return sorted(out, key=lambda x: (x.price_diff, x.catalog_id))


def _attraction_options(pkg: Package, day: date) -> list[Option]:
    if not date.fromisoformat(pkg.start_date) <= day < date.fromisoformat(pkg.end_date):
        raise ChangeError("Attractions can be added from the arrival day to the day before the return.")
    city = city_of_night(pkg, day)
    store = get_store()
    adults, children = travelers(pkg)
    in_pkg = {i.catalog_id for i in items_of(pkg, "attraction")}
    out = []
    for a in store.get_attractions_in_city(city or ""):
        if a.attraction_id in in_pkg:
            continue
        start = find_slot(pkg, a, day)
        if start is None:
            continue
        price = calculate_attraction_price(a.price_per_person, a.child_price, adults, children)
        res = _try(pkg, Change(type="add_attraction", date=day.isoformat(), attraction_id=a.attraction_id,
                               start=format_iso_hm(start)))
        if res is None:
            continue
        out.append(Option(
            kind="attraction", catalog_id=a.attraction_id, label=a.name, price_inr=price, price_diff=price,
            start=format_iso_hm(start),
            details={"category": a.category, "visit_minutes": a.visit_minutes, "child_friendly": a.child_friendly,
                     "open": f"{a.open_from}–{a.open_until}", "image": a.image}))
    return sorted(out, key=lambda x: (x.price_diff, x.start, x.catalog_id))

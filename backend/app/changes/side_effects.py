"""Apply a change and its knock-on effects (M6, G1).  (Person A)

apply_change() returns a NEW package (the input is never modified) plus plain-English side effects and
warnings. It does NOT validate: changes/apply.py (Person B) runs validate() and refuses with 409 if needed.
Raises ChangeError for requests that cannot be applied at all (unknown ID, wrong item) -> B returns 422.
"""

from __future__ import annotations

import copy
from datetime import date, datetime, timedelta

from app.builder.hotels import smallest_k
from app.builder.transfers import TransferChoice, arrival_options, return_options
from app.catalog.models import Attraction
from app.catalog.store import get_store
from app.core.package_model import Change, ChangeResult, Item, Package
from app.core.timeutil import format_iso_hm, parse_hhmm
from app.pricing.calculator import calculate_attraction_price, calculate_flight_price, calculate_hotel_price
from app.rules.checks.attractions import fits_opening

VISIT_GAP = 30          # minutes between two visits on one day
DAY_START = "09:00"     # earliest visit on a full day


class ChangeError(ValueError):
    """The change cannot be applied (unknown ID, wrong item type, …)."""


# ------------------------------------------------------------------ package helpers

def travelers(pkg: Package) -> tuple[int, int]:
    return pkg.traveler.adults, len(pkg.traveler.child_ages)


def items_of(pkg: Package, kind: str) -> list[Item]:
    return [i for i in pkg.items if i.type == kind]


def flight_items(pkg: Package) -> tuple[Item, Item]:
    flights = sorted(items_of(pkg, "flight"), key=lambda i: i.start)
    if len(flights) != 2:
        raise ChangeError("The package must have exactly one arrival and one return flight.")
    return flights[0], flights[1]


def hotel_items(pkg: Package) -> list[Item]:
    return sorted(items_of(pkg, "hotel"), key=lambda i: i.start)


def airport_transfer_items(pkg: Package) -> tuple[Item | None, Item | None]:
    store = get_store()
    ats = sorted((i for i in items_of(pkg, "transfer")
                  if (t := store.get_transfer(i.catalog_id)) and t.type.startswith("AIRPORT")), key=lambda i: i.start)
    return (ats[0] if ats else None), (ats[-1] if len(ats) > 1 else None)


def next_item_id(pkg: Package) -> str:
    nums = [int(i.item_id[1:]) for i in pkg.items if i.item_id[1:].isdigit()]
    return f"i{max(nums, default=0) + 1}"


def sort_items(pkg: Package) -> None:
    """Time order for display; hotel check-ins sort at 15:00 on their date."""
    def key(i: Item):
        when = datetime.fromisoformat(i.start) if "T" in i.start else datetime.fromisoformat(i.start) + timedelta(hours=15)
        return when, {"flight": 0, "transfer": 1, "hotel": 3, "attraction": 4}.get(i.type, 5)
    pkg.items.sort(key=key)


def city_of_night(pkg: Package, day: date) -> str | None:
    for h in hotel_items(pkg):
        if date.fromisoformat(h.start) <= day < date.fromisoformat(h.end):
            return h.city
    return None


def reach_city_time(pkg: Package, day: date) -> datetime | None:
    """When the traveler reaches the city on the arrival day / a change day (else None)."""
    store = get_store()
    for i in items_of(pkg, "transfer"):
        t = store.get_transfer(i.catalog_id)
        if not t or not i.end or not i.start.startswith(day.isoformat()):
            continue
        if t.type.startswith("AIRPORT") and day.isoformat() == pkg.start_date:
            return datetime.fromisoformat(i.end)
        if t.from_city and t.to_city:
            return datetime.fromisoformat(i.end)
    return None


def _set_transfer(item: Item, choice: TransferChoice, adults: int, children: int) -> None:
    t = choice.transfer
    item.catalog_id, item.name = t.transfer_id, t.name
    item.start, item.end = format_iso_hm(choice.start), format_iso_hm(choice.end)
    item.quantity = -(-(adults + children) // t.max_passengers) if t.pricing == "PER_VEHICLE" else adults + children
    item.price_inr = choice.price


# ------------------------------------------------------------------ attraction slots

def find_slot(pkg: Package, attraction: Attraction, day: date, ignore_item: str | None = None) -> datetime | None:
    """Earliest start on `day` that fits opening hours, is after reaching the city, and keeps a 30-minute gap
    to the day's other visits."""
    store = get_store()
    day_start = datetime.combine(day, datetime.min.time()) + timedelta(minutes=parse_hhmm(DAY_START))
    reach = reach_city_time(pkg, day)
    earliest = max(day_start, reach) if reach else day_start
    busy = []
    for i in items_of(pkg, "attraction"):
        if i.item_id != ignore_item and i.start.startswith(day.isoformat()):
            a = store.get_attraction(i.catalog_id)
            s = datetime.fromisoformat(i.start)
            busy.append((s, s + timedelta(minutes=a.visit_minutes if a else 0)))
    opens = datetime.combine(day, datetime.min.time()) + timedelta(minutes=parse_hhmm(attraction.open_from))
    candidates = sorted({max(earliest, opens)} | {e + timedelta(minutes=VISIT_GAP) for _, e in busy})
    for start in candidates:
        if start < earliest or start.date() != day:
            continue
        if start.minute % 5:                       # round up to a 5-minute mark
            start += timedelta(minutes=5 - start.minute % 5)
        end = start + timedelta(minutes=attraction.visit_minutes)
        clash = any(start < e + timedelta(minutes=VISIT_GAP) and s < end + timedelta(minutes=VISIT_GAP)
                    for s, e in busy)
        if not clash and fits_opening(attraction, start) is None:
            return start
    return None


# ------------------------------------------------------------------ the four changes

def _change_hotel(pkg: Package, ch: Change, fx: list[str], warn: list[str]) -> None:
    store = get_store()
    adults, children = travelers(pkg)
    stays = hotel_items(pkg)
    item = next((h for h in stays if h.city == ch.city), None)
    if item is None:
        raise ChangeError(f"The package has no hotel in {ch.city}.")
    hotel, room = store.get_hotel(ch.hotel_id or ""), store.get_room(ch.room_id or "")
    if not hotel or not room or room.hotel_id != hotel.hotel_id:
        raise ChangeError("Unknown hotel or room type, or the room is not in that hotel.")
    if hotel.city != item.city:
        raise ChangeError(f"{hotel.name} is in {hotel.city}, not {item.city}.")
    k = smallest_k(adults, children, room)
    if k is None:
        raise ChangeError(f"{room.name} cannot fit {adults} adult(s) and {children} child(ren).")
    nights = (date.fromisoformat(item.end) - date.fromisoformat(item.start)).days
    item.catalog_id, item.name, item.room_id, item.quantity = hotel.hotel_id, hotel.name, room.room_id, k
    item.price_inr = calculate_hotel_price(room.price_per_night, k, nights)

    arr_f, ret_f = flight_items(pkg)
    at_arr, at_ret = airport_transfer_items(pkg)
    if item is stays[0] and at_arr:
        _retime_arrival(pkg, store.get_flight(arr_f.catalog_id), hotel, at_arr, fx, warn)
    if item is stays[-1] and at_ret:
        _retime_return(store.get_flight(ret_f.catalog_id), hotel, at_ret, adults, children, fx, warn)


def _retime_arrival(pkg, flight, hotel, at_item: Item, fx: list[str], warn: list[str]) -> None:
    adults, children = travelers(pkg)
    opts = arrival_options(flight, hotel, adults, children)
    if not opts:
        fx.append(f"No airport transfer from {flight.to_airport} reaches {hotel.name} in time; "
                  "the arrival transfer could not be updated.")
        return
    old = (at_item.catalog_id, at_item.start)
    _set_transfer(at_item, opts[0], adults, children)
    if (at_item.catalog_id, at_item.start) != old:
        fx.append(f"Arrival transfer is now {at_item.name}, pickup {opts[0].start:%H:%M}.")
    if opts[0].end.strftime("%H:%M") < hotel.check_in_from:
        warn.append(f"You reach {hotel.name} at {opts[0].end:%H:%M}; check-in opens at {hotel.check_in_from}.")


def _retime_return(flight, hotel, at_item: Item, adults: int, children: int, fx: list[str],
                   warn: list[str] | None = None) -> None:
    opts = return_options(flight, hotel, adults, children)
    if not opts:
        fx.append(f"No transfer from {hotel.name} reaches {flight.from_airport} 3 hours before the flight; "
                  "the return transfer could not be updated.")
        return
    old = (at_item.catalog_id, at_item.start)
    _set_transfer(at_item, opts[0], adults, children)
    if (at_item.catalog_id, at_item.start) != old:
        fx.append(f"Return transfer is now {at_item.name}, leaving the hotel at {opts[0].start:%H:%M}.")
    # G1: leaving the hotel after check-out means a late check-out (or luggage storage) is needed
    if warn is not None and hotel.check_out_until and opts[0].start.strftime("%H:%M") > hotel.check_out_until:
        warn.append(f"You leave {hotel.name} at {opts[0].start:%H:%M} but check-out is by {hotel.check_out_until}; "
                    "ask the hotel for a late check-out or to keep your luggage.")


def _change_flight(pkg: Package, ch: Change, fx: list[str], warn: list[str]) -> None:
    store = get_store()
    adults, children = travelers(pkg)
    flight = store.get_flight(ch.flight_id or "")
    if flight is None:
        raise ChangeError(f"Unknown flight '{ch.flight_id}'.")
    if ch.leg not in ("arrival", "return"):
        raise ChangeError("leg must be 'arrival' or 'return'.")
    arr_item, ret_item = flight_items(pkg)
    item = arr_item if ch.leg == "arrival" else ret_item
    item.catalog_id = flight.flight_id
    item.name = f"{flight.flight_number} {flight.from_airport} to {flight.to_airport}"
    item.start = format_iso_hm(datetime.fromisoformat(flight.departure_local))
    item.end = format_iso_hm(datetime.fromisoformat(flight.arrival_local))
    item.quantity, item.price_inr = adults + children, calculate_flight_price(flight.price_per_seat, adults + children)

    stays = hotel_items(pkg)
    at_arr, at_ret = airport_transfer_items(pkg)
    if ch.leg == "arrival":
        if at_arr and stays:
            _retime_arrival(pkg, flight, store.get_hotel(stays[0].catalog_id), at_arr, fx, warn)
        _drop_unreachable_visits(pkg, date.fromisoformat(pkg.start_date), fx)
    elif at_ret and stays:
        _retime_return(flight, store.get_hotel(stays[-1].catalog_id), at_ret, adults, children, fx, warn)


def _drop_unreachable_visits(pkg: Package, day: date, fx: list[str]) -> None:
    """G1: after a later arrival, remove arrival-day visits that now start before the traveler arrives."""
    reach = reach_city_time(pkg, day)
    if reach is None:
        return
    keep = []
    for i in pkg.items:
        if i.type == "attraction" and i.start.startswith(day.isoformat()) and datetime.fromisoformat(i.start) < reach:
            fx.append(f"Removed {i.name}: it started at {i.start[11:]}, before you now reach the city at {reach:%H:%M}.")
        else:
            keep.append(i)
    pkg.items = keep


def _add_attraction(pkg: Package, ch: Change, fx: list[str], warn: list[str]) -> None:
    store = get_store()
    adults, children = travelers(pkg)
    a = store.get_attraction(ch.attraction_id or "")
    if a is None:
        raise ChangeError(f"Unknown attraction '{ch.attraction_id}'.")
    try:
        day = date.fromisoformat(ch.date or "")
    except ValueError as exc:
        raise ChangeError("date must be 'YYYY-MM-DD'.") from exc
    if ch.start:
        start = datetime.fromisoformat(ch.start if "T" in ch.start else f"{day.isoformat()}T{ch.start}")
    else:
        start = find_slot(pkg, a, day)
        if start is None:
            # no free slot: put it at opening time so validate() explains the exact problem
            start = datetime.combine(day, datetime.min.time()) + timedelta(minutes=parse_hhmm(a.open_from))
        else:
            fx.append(f"{a.name} scheduled at {start:%H:%M}.")
    pkg.items.append(Item(
        item_id=next_item_id(pkg), type="attraction", name=a.name, city=a.city, catalog_id=a.attraction_id,
        start=format_iso_hm(start), end=format_iso_hm(start + timedelta(minutes=a.visit_minutes)),
        quantity=adults + children,
        price_inr=calculate_attraction_price(a.price_per_person, a.child_price, adults, children)))


def _remove_attraction(pkg: Package, ch: Change, fx: list[str], warn: list[str]) -> None:
    item = next((i for i in pkg.items if i.item_id == ch.item_id), None)
    if item is None or item.type != "attraction":
        raise ChangeError(f"'{ch.item_id}' is not an attraction in this package.")
    pkg.items.remove(item)
    day = item.start[:10]
    if not any(i.type == "attraction" and i.start.startswith(day) for i in pkg.items):
        warn.append(f"{date.fromisoformat(day):%d %b} now has no attraction planned.")


_HANDLERS = {"hotel": _change_hotel, "flight": _change_flight,
             "add_attraction": _add_attraction, "remove_attraction": _remove_attraction}


def apply_change(pkg: Package, change: Change) -> ChangeResult:
    if change.type not in _HANDLERS:
        raise ChangeError(f"Unknown change type '{change.type}'.")
    new = copy.deepcopy(pkg)
    side_effects: list[str] = []
    warnings: list[str] = []
    _HANDLERS[change.type](new, change, side_effects, warnings)
    sort_items(new)
    return ChangeResult(package=new, side_effects=side_effects, warnings=warnings)

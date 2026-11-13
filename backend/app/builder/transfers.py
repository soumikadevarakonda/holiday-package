"""Transfer choice with timing: airport pickup (+60), airport drop (−180), inter-city slot on the grid."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.catalog.models import Flight, Hotel, Transfer
from app.catalog.store import get_store
from app.core.timeutil import parse_hhmm, time_in_window
from app.pricing.calculator import calculate_transfer_price
from app.rules.checks.airport_transfers import AT_AIRPORT_BEFORE_DEP, PICKUP_AFTER_LANDING
from app.rules.checks.intercity import on_grid

INTERCITY_EARLIEST = "10:00"   # T12: first grid slot at or after 10:00 (after a typical checkout)


@dataclass(frozen=True)
class TransferChoice:
    transfer: Transfer
    start: datetime
    price: int

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.transfer.duration_minutes)


def _price(t: Transfer, adults: int, children: int) -> int:
    return calculate_transfer_price(t.pricing, t.price, t.child_price, t.max_passengers, adults, children)


def _minute(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def _at(day: date, minute: int) -> datetime:
    return datetime.combine(day, datetime.min.time()) + timedelta(minutes=minute)


def _serves_hotel(t: Transfer, airport: str, hotel: Hotel) -> bool:
    return t.airport_code == airport and t.city == hotel.city and (t.area is None or t.area == hotel.area)


def arrival_options(flight: Flight, hotel: Hotel, adults: int, children: int) -> list[TransferChoice]:
    """Valid airport → hotel transfers, cheapest first. Pickup = landing + 60, or the first service time after."""
    landing = datetime.fromisoformat(flight.arrival_local)
    earliest = landing + timedelta(minutes=PICKUP_AFTER_LANDING)
    out = []
    for t in get_store().get_airport_transfers(flight.to_airport, hotel.city):
        if not _serves_hotel(t, flight.to_airport, hotel):
            continue
        pickup = earliest
        if not time_in_window(_minute(pickup), t.service_from, t.service_until):
            opens = _at(pickup.date(), parse_hhmm(t.service_from))
            if opens <= pickup:
                opens += timedelta(days=1)
            if opens.date() != pickup.date():   # don't wait overnight
                continue
            pickup = opens
        out.append(TransferChoice(t, pickup, _price(t, adults, children)))
    return sorted(out, key=lambda c: (c.price, c.start, c.transfer.transfer_id))


def return_options(flight: Flight, hotel: Hotel, adults: int, children: int) -> list[TransferChoice]:
    """Valid hotel → airport transfers, cheapest first. Leave as late as allowed: dep − 180 − duration."""
    departure = datetime.fromisoformat(flight.departure_local)
    out = []
    for t in get_store().get_airport_transfers(flight.from_airport, hotel.city):
        if not _serves_hotel(t, flight.from_airport, hotel):
            continue
        leave = departure - timedelta(minutes=AT_AIRPORT_BEFORE_DEP + t.duration_minutes)
        if not time_in_window(_minute(leave), t.service_from, t.service_until):
            # leave earlier, at the last service time of the same day
            until = parse_hhmm(t.service_until)
            closes = _at(leave.date(), min(until, 1439))
            if parse_hhmm(t.service_from) > until or closes > leave or not time_in_window(
                    _minute(closes), t.service_from, t.service_until):
                continue
            leave = closes
        out.append(TransferChoice(t, leave, _price(t, adults, children)))
    return sorted(out, key=lambda c: (c.price, -c.start.timestamp(), c.transfer.transfer_id))


def intercity_options(from_city: str, to_city: str, day: date, adults: int, children: int) -> list[TransferChoice]:
    """Link transfers old → new city on `day`: first valid slot at or after 10:00, cheapest first."""
    store = get_store()
    allowed = set(store.indexes.link_transfer_ids.get((from_city, to_city), []))
    out = []
    for t in store.get_intercity_transfers(from_city, to_city):
        if t.transfer_id not in allowed:
            continue
        earliest = parse_hhmm(INTERCITY_EARLIEST)
        start = parse_hhmm(t.service_from)
        if t.frequency_minutes:
            slot = start + max(0, -(-(earliest - start) // t.frequency_minutes)) * t.frequency_minutes
        else:
            slot = max(earliest, start)
        if slot >= 1440 or not time_in_window(slot, t.service_from, t.service_until) or not on_grid(
                slot, t.service_from, t.frequency_minutes):
            continue
        out.append(TransferChoice(t, _at(day, slot), _price(t, adults, children)))
    return sorted(out, key=lambda c: (c.price, c.start, c.transfer.transfer_id))

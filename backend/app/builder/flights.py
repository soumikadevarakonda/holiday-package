"""Arrival / return flight candidates by local date and seats."""

from __future__ import annotations

from datetime import date

from app.catalog.models import Flight
from app.catalog.store import get_store


def arrival_flights(home_airport: str, country_cities: set[str], start: date, travelers: int) -> list[Flight]:
    """Flights from home that land on the start date (local) at an airport serving a city of the country."""
    store = get_store()
    out = []
    for f in store.get_arrival_flights(home_airport, start.isoformat()):
        ap = store.get_airport(f.to_airport)
        if ap and set(ap.serves_cities) & country_cities and f.seats_left >= travelers:
            out.append(f)
    return sorted(out, key=lambda f: (f.price_per_seat, f.arrival_local, f.flight_id))


def return_flights(home_airport: str, country_cities: set[str], end: date, travelers: int) -> list[Flight]:
    """Flights home that depart on the return day (local) from an airport serving a city of the country."""
    store = get_store()
    out = []
    for f in store.get_return_flights(home_airport, end.isoformat()):
        ap = store.get_airport(f.from_airport)
        if ap and set(ap.serves_cities) & country_cities and f.seats_left >= travelers:
            out.append(f)
    return sorted(out, key=lambda f: (f.price_per_seat, f.departure_local, f.flight_id))


def all_flights_on(home_airport: str, country_cities: set[str], start: date, end: date) -> tuple[int, int]:
    """Counts ignoring seats, for failure messages."""
    store = get_store()
    def serves(code: str) -> bool:
        ap = store.get_airport(code)
        return bool(ap and set(ap.serves_cities) & country_cities)
    arr = [f for f in store.get_arrival_flights(home_airport, start.isoformat()) if serves(f.to_airport)]
    ret = [f for f in store.get_return_flights(home_airport, end.isoformat()) if serves(f.from_airport)]
    return len(arr), len(ret)

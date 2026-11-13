"""F1–F4: one arrival and one return flight, right dates and airports, enough seats."""

from __future__ import annotations

from app.core.package_model import Violation
from app.rules.checks.dates import fmt
from app.rules.context import Ctx, parse_d


def check(ctx: Ctx, seats_used: dict[str, int] | None = None) -> list[Violation]:
    """seats_used: S2, seats already booked per flight_id (effective seats = seats_left - used)."""
    v: list[Violation] = []
    seats_used = seats_used or {}

    # F1 — exactly one arrival and one return
    if len(ctx.flights) != 2:
        v.append(Violation("F1", None, f"The package has {len(ctx.flights)} flight(s); it needs exactly one "
                                       "arrival flight and one return flight."))
        return v
    arr, ret = ctx.arrival.flight, ctx.ret.flight
    if arr.from_airport != ctx.home_airport:
        v.append(Violation("F1", ctx.arrival.item.item_id,
                           f"The arrival flight leaves from {arr.from_airport}, not from {ctx.home_airport}."))
    if ret.to_airport != ctx.home_airport:
        v.append(Violation("F3", ctx.ret.item.item_id,
                           f"The return flight lands at {ret.to_airport}, not at {ctx.home_airport}."))

    first_city = ctx.stays[0].hotel.city if ctx.stays else None
    last_city = ctx.stays[-1].hotel.city if ctx.stays else None
    store = ctx.store

    # F2 — lands on S (local) at an airport serving the first city
    if parse_d(arr.arrival_local) != ctx.start:
        v.append(Violation("F2", ctx.arrival.item.item_id, f"The arrival flight lands on "
                           f"{fmt(parse_d(arr.arrival_local))}, not on the start date {fmt(ctx.start)}."))
    to_ap = store.get_airport(arr.to_airport)
    if first_city and (not to_ap or first_city not in to_ap.serves_cities):
        v.append(Violation("F2", ctx.arrival.item.item_id,
                           f"{arr.to_airport} does not serve {first_city}, the first city."))

    # F3 — leaves on L (local) from an airport serving the last city
    if parse_d(ret.departure_local) != ctx.end:
        v.append(Violation("F3", ctx.ret.item.item_id, f"The return flight leaves on "
                           f"{fmt(parse_d(ret.departure_local))}, not on the return day {fmt(ctx.end)}."))
    from_ap = store.get_airport(ret.from_airport)
    if last_city and (not from_ap or last_city not in from_ap.serves_cities):
        v.append(Violation("F3", ctx.ret.item.item_id,
                           f"{ret.from_airport} does not serve {last_city}, the last city."))

    # F4 — a seat for every traveler
    for leg in (ctx.arrival, ctx.ret):
        left = leg.flight.seats_left - seats_used.get(leg.flight.flight_id, 0)
        if left < ctx.travelers:
            v.append(Violation("F4", leg.item.item_id, f"{leg.flight.flight_number} has {left} seat(s) left "
                                                        f"for {ctx.travelers} travelers."))
    return v

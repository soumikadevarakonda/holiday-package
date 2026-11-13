"""AT1–AT4: airport → first hotel and last hotel → airport, timing and service hours."""

from __future__ import annotations

from datetime import timedelta

from app.core.package_model import Violation
from app.core.timeutil import time_in_window
from app.rules.context import Ctx, TransferUse, parse_dt

PICKUP_AFTER_LANDING = 60      # AT2
AT_AIRPORT_BEFORE_DEP = 180    # AT3


def _hhmm(dt) -> str:
    return dt.strftime("%H:%M")


def _serves(use: TransferUse, airport: str, city: str, area: str) -> str | None:
    t = use.transfer
    if t.airport_code != airport:
        return f"{t.name} runs from {t.airport_code}, not {airport}."
    if t.city != city:
        return f"{t.name} serves {t.city}, not {city}."
    if t.area is not None and t.area != area:
        return f"{t.name} serves the {t.area} area, but the hotel is in {area}."
    return None


def _in_hours(use: TransferUse, rule: str, what: str) -> list[Violation]:
    t = use.transfer
    if not time_in_window(_hhmm(use.start), t.service_from, t.service_until):
        return [Violation(rule, use.item.item_id, f"{what} at {_hhmm(use.start)} is outside {t.name} service "
                                                  f"hours ({t.service_from}–{t.service_until}).")]
    return []


def check(ctx: Ctx) -> list[Violation]:
    v: list[Violation] = []
    if not ctx.arrival or not ctx.stays:
        return v
    # AT1 — exactly one transfer at each end
    if len(ctx.airport_transfers) != 2:
        v.append(Violation("AT1", None, f"The package has {len(ctx.airport_transfers)} airport transfer(s); it "
                                        "needs one from the arrival airport and one to the return airport."))
        return v
    arr_use, ret_use = ctx.airport_transfers
    first, last = ctx.stays[0].hotel, ctx.stays[-1].hotel
    arr_f, ret_f = ctx.arrival.flight, ctx.ret.flight

    if msg := _serves(arr_use, arr_f.to_airport, first.city, first.area):
        v.append(Violation("AT1", arr_use.item.item_id, msg))
    if msg := _serves(ret_use, ret_f.from_airport, last.city, last.area):
        v.append(Violation("AT1", ret_use.item.item_id, msg))

    # AT2 — pickup ≥ landing + 60
    landing = parse_dt(arr_f.arrival_local)
    if arr_use.start < landing + timedelta(minutes=PICKUP_AFTER_LANDING):
        v.append(Violation("AT2", arr_use.item.item_id, f"Pickup at {_hhmm(arr_use.start)} is less than 60 minutes "
                                                         f"after landing at {_hhmm(landing)}."))
    # AT3 — at the airport ≤ departure − 180
    departure = parse_dt(ret_f.departure_local)
    at_airport = ret_use.start + timedelta(minutes=ret_use.transfer.duration_minutes)
    if at_airport > departure - timedelta(minutes=AT_AIRPORT_BEFORE_DEP):
        v.append(Violation("AT3", ret_use.item.item_id, f"Leaving the hotel at {_hhmm(ret_use.start)} reaches the "
                           f"airport at {_hhmm(at_airport)}, less than 180 minutes before the "
                           f"{_hhmm(departure)} flight."))
    # AT4 — pickup and hotel leave time inside service hours
    v += _in_hours(arr_use, "AT4", "Pickup")
    v += _in_hours(ret_use, "AT4", "Leaving the hotel")
    return v

"""CT1: one link transfer old city → new city on each change day, in service hours, on the departure grid."""

from __future__ import annotations

from app.core.package_model import Violation
from app.core.timeutil import parse_hhmm, time_in_window
from app.rules.checks.dates import fmt
from app.rules.context import Ctx


def on_grid(minute_of_day: int, service_from: str, frequency: int | None) -> bool:
    if not frequency:
        return True
    return (minute_of_day - parse_hhmm(service_from)) % 1440 % frequency == 0


def check(ctx: Ctx) -> list[Violation]:
    v: list[Violation] = []
    used = set()
    for prev, nxt in zip(ctx.stays, ctx.stays[1:]):
        day, old, new = nxt.check_in, prev.hotel.city, nxt.hotel.city
        allowed = ctx.store.indexes.link_transfer_ids.get((old, new), [])
        uses = [u for u in ctx.intercity_transfers if u.start.date() == day]
        if not allowed:
            v.append(Violation("CT1", nxt.item.item_id, f"There is no transfer link from {old} to {new}."))
            continue
        matching = [u for u in uses if u.transfer.transfer_id in allowed
                    and (u.transfer.from_city, u.transfer.to_city) == (old, new)]
        if len(matching) != 1:
            v.append(Violation("CT1", nxt.item.item_id, f"On {fmt(day)} the package needs exactly one transfer "
                                                         f"from {old} to {new}; it has {len(matching)}."))
            continue
        u = matching[0]
        used.add(u.item.item_id)
        t, hhmm = u.transfer, u.start.strftime("%H:%M")
        if not time_in_window(hhmm, t.service_from, t.service_until):
            v.append(Violation("CT1", u.item.item_id, f"{t.name} at {hhmm} is outside its service hours "
                                                       f"({t.service_from}–{t.service_until})."))
        elif not on_grid(parse_hhmm(hhmm), t.service_from, t.frequency_minutes):
            v.append(Violation("CT1", u.item.item_id, f"{t.name} leaves every {t.frequency_minutes} minutes from "
                                                       f"{t.service_from}; there is no departure at {hhmm}."))
    for u in ctx.intercity_transfers:
        if u.item.item_id not in used:
            v.append(Violation("CT1", u.item.item_id, f"{u.transfer.name} on {fmt(u.start.date())} is not on a "
                                                       "city-change day of this plan."))
    return v

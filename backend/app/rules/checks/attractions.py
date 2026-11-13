"""A1–A4: attractions in the right city, open, no overlap, once only, 1–2 per full day, timing."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.core.package_model import Violation
from app.core.timeutil import parse_hhmm, weekday_of
from app.rules.checks.dates import fmt
from app.rules.context import Ctx, Visit


def fits_opening(a, start: datetime) -> str | None:
    """A1 timing for one visit; returns the problem or None."""
    day = start.date()
    if weekday_of(day) not in a.open_days:
        return f"{a.name} is closed on {weekday_of(day).title()}days ({fmt(day)})."
    if day.isoformat() in a.closed_dates:
        return f"{a.name} is closed on {fmt(day)}."
    s = start.hour * 60 + start.minute
    if s < parse_hhmm(a.open_from) or s + a.visit_minutes > parse_hhmm(a.open_until):
        return (f"{a.name} opens {a.open_from}–{a.open_until}; a {a.visit_minutes}-minute visit from "
                f"{start:%H:%M} does not fit.")
    return None


def _reach_city_time(ctx: Ctx, day) -> datetime | None:
    """When the traveler reaches the city on the arrival day or a change day (A4)."""
    if day == ctx.start and ctx.airport_transfers:
        use = ctx.airport_transfers[0]
        return use.start + timedelta(minutes=use.transfer.duration_minutes)
    for use in ctx.intercity_transfers:
        if use.start.date() == day:
            return use.start + timedelta(minutes=use.transfer.duration_minutes)
    return None


def check(ctx: Ctx, initial: bool = False) -> list[Violation]:
    v: list[Violation] = []
    change_days = set(ctx.change_days)
    by_day: dict = {}

    seen: set[str] = set()
    for vis in ctx.visits:
        a, day, iid = vis.attraction, vis.start.date(), vis.item.item_id
        by_day.setdefault(day, []).append(vis)
        # A2 — each attraction once
        if a.attraction_id in seen:
            v.append(Violation("A2", iid, f"{a.name} is in the package more than once."))
        seen.add(a.attraction_id)
        # A4 — none on the return day / outside the trip
        if not ctx.start <= day < ctx.end:
            v.append(Violation("A4", iid, f"{a.name} on {fmt(day)} is outside the stay "
                                          "(no attractions on the return day)."))
            continue
        # A1 — city of that night's hotel, open, fits hours
        city = ctx.city_of_night(day)
        if city and a.city != city:
            v.append(Violation("A1", iid, f"{a.name} is in {a.city}, but on {fmt(day)} the hotel is in {city}."))
        if msg := fits_opening(a, vis.start):
            v.append(Violation("A1", iid, msg))
        # A4 — after reaching the city on arrival / change days
        if day == ctx.start or day in change_days:
            reach = _reach_city_time(ctx, day)
            if reach and vis.start < reach:
                v.append(Violation("A4", iid, f"{a.name} starts at {vis.start:%H:%M}, before the traveler "
                                              f"reaches {city} at {reach:%H:%M}."))

    # A2 — no overlaps on a day
    for day, visits in by_day.items():
        visits.sort(key=lambda x: x.start)
        for x, y in zip(visits, visits[1:]):
            if y.start < x.end:
                v.append(Violation("A2", y.item.item_id, f"{y.attraction.name} ({y.start:%H:%M}) overlaps "
                                                          f"{x.attraction.name} (until {x.end:%H:%M}) on {fmt(day)}."))

    # A3 — first package: 1–2 attractions every full day
    if initial:
        for i in range(1, ctx.nights):
            day = ctx.start + timedelta(days=i)
            if day in change_days:
                continue
            n = len(by_day.get(day, []))
            if not 1 <= n <= 2:
                v.append(Violation("A3", None, f"{fmt(day)} is a full day with {n} attraction(s); "
                                               "the first package needs 1–2."))
    return v


def full_days(ctx: Ctx) -> list:
    change = set(ctx.change_days)
    return [ctx.start + timedelta(days=i) for i in range(1, ctx.nights)
            if ctx.start + timedelta(days=i) not in change]


__all__ = ["check", "fits_opening", "full_days", "Visit"]

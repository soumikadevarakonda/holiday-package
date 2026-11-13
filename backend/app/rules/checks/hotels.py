"""H1–H4: a hotel every night, one hotel + room type per city, rooms fit, rooms left."""

from __future__ import annotations

from datetime import timedelta

from app.core.package_model import Violation
from app.rules.checks.dates import fmt
from app.rules.context import Ctx


def rooms_fit(adults: int, children: int, k: int, max_adults: int, max_children: int) -> bool:
    """H3 for k rooms of one type."""
    return k >= 1 and adults >= k and adults <= k * max_adults and adults + children <= k * (max_adults + max_children)


def check(ctx: Ctx, rooms_used: dict[tuple[str, str], int] | None = None) -> list[Violation]:
    """rooms_used: S2, rooms already booked per (room_id, 'YYYY-MM-DD')."""
    v: list[Violation] = []
    rooms_used = rooms_used or {}

    # H1 — exactly one hotel each night S … L−1, none on L
    covered: dict = {}
    for s in ctx.stays:
        for night in s.nights:
            covered[night] = covered.get(night, 0) + 1
    for i in range(ctx.nights):
        night = ctx.start + timedelta(days=i)
        if covered.get(night, 0) != 1:
            v.append(Violation("H1", None, f"The night of {fmt(night)} has {covered.get(night, 0)} hotel(s); "
                                           "it needs exactly one."))
    for night in covered:
        if not ctx.start <= night < ctx.end:
            v.append(Violation("H1", None, f"There is a hotel night on {fmt(night)}, outside the trip "
                                           f"({fmt(ctx.start)} to {fmt(ctx.end)}, no night on the return day)."))

    # H2 — one hotel item per city (one hotel, one room type for all its nights)
    cities: dict[str, int] = {}
    for s in ctx.stays:
        cities[s.hotel.city] = cities.get(s.hotel.city, 0) + 1
        if s.item.city != s.hotel.city:
            v.append(Violation("H2", s.item.item_id, f"{s.hotel.name} is in {s.hotel.city}, not {s.item.city}."))
    for city, n in cities.items():
        if n > 1:
            v.append(Violation("H2", None, f"{city} has {n} hotel bookings; use one hotel and one room type "
                                           "for all its nights."))

    for s in ctx.stays:
        k, r = s.item.quantity, s.room
        # H3 — k rooms fit the travelers
        if not rooms_fit(ctx.adults, ctx.children, k, r.max_adults, r.max_children):
            v.append(Violation("H3", s.item.item_id, f"{k} × {r.name} (max {r.max_adults} adults + "
                               f"{r.max_children} children each) does not fit {ctx.adults} adult(s) and "
                               f"{ctx.children} child(ren)."))
        # H4 — rooms left every night
        for night in s.nights:
            key = (r.room_id, night.isoformat())
            left = ctx.store.get_rooms_left(*key) - rooms_used.get(key, 0)
            if left < k:
                v.append(Violation("H4", s.item.item_id, f"{s.hotel.name} has {left} {r.name} room(s) left on "
                                                          f"{fmt(night)}; the package needs {k}."))
    return v

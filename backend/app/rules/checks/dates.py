"""D1–D3: trip length and window, cities in the country, the city plan."""

from __future__ import annotations

from datetime import date

from app.core.package_model import Violation
from app.rules.context import Ctx


def fmt(d: date) -> str:
    return d.strftime("%d %b %Y").lstrip("0")


def check(ctx: Ctx) -> list[Violation]:
    v: list[Violation] = []
    rules = ctx.store.rules
    first_night, last_dep = date.fromisoformat(rules.first_night), date.fromisoformat(rules.last_departure)

    # D1 — nights and data window
    if not rules.min_nights <= ctx.nights <= rules.max_nights:
        v.append(Violation("D1", None, f"The trip has {ctx.nights} nights; it must be "
                                       f"{rules.min_nights} to {rules.max_nights}."))
    if ctx.start < first_night:
        v.append(Violation("D1", None, f"The first night ({fmt(ctx.start)}) is before {fmt(first_night)}."))
    if ctx.end > last_dep:
        v.append(Violation("D1", None, f"The return day ({fmt(ctx.end)}) is after the last flight "
                                       f"date {fmt(last_dep)}."))

    # D2 — every city in the chosen country
    plan_cities = [c.city for c in ctx.pkg.city_plan] or [s.hotel.city for s in ctx.stays]
    for city in plan_cities:
        if city not in ctx.country_cities:
            v.append(Violation("D2", None, f"{city} is not a destination city in {ctx.pkg.country}."))

    # D3 — ≥ min nights per city, in a row, each city once, nights sum to N
    seen: set[str] = set()
    for s in ctx.stays:
        n = len(s.nights)
        if n < rules.min_nights_per_city:
            v.append(Violation("D3", s.item.item_id, f"{s.hotel.city} has {n} night(s); each city needs at "
                                                      f"least {rules.min_nights_per_city} nights in a row."))
        if s.hotel.city in seen:
            v.append(Violation("D3", s.item.item_id, f"{s.hotel.city} appears more than once in the plan."))
        seen.add(s.hotel.city)
    plan = ctx.pkg.city_plan
    if plan:
        if sum(c.nights for c in plan) != ctx.nights:
            v.append(Violation("D3", None, f"The city plan has {sum(c.nights for c in plan)} nights, "
                                           f"but the trip has {ctx.nights}."))
        if [(c.city, c.nights) for c in plan] != [(s.hotel.city, len(s.nights)) for s in ctx.stays]:
            v.append(Violation("D3", None, "The hotels do not match the city plan (cities, order or nights)."))
    return v

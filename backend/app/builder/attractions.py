"""Attraction schedule: one visit per full day, free and child-friendly first, no attraction used twice.

Days are matched to attractions with augmenting paths (Kuhn), so a later day never loses its only
open attraction to an earlier day: the schedule is found whenever one exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.catalog.models import Attraction
from app.catalog.store import get_store
from app.core.timeutil import parse_hhmm
from app.pricing.calculator import calculate_attraction_price
from app.rules.checks.attractions import fits_opening

DAY_START = "09:00"   # full days: earliest visit start


@dataclass(frozen=True)
class VisitChoice:
    attraction: Attraction
    start: datetime
    price: int

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.attraction.visit_minutes)


def _slot(a: Attraction, day: date) -> datetime | None:
    start_min = max(parse_hhmm(DAY_START), parse_hhmm(a.open_from))
    start = datetime.combine(day, datetime.min.time()) + timedelta(minutes=start_min)
    return None if fits_opening(a, start) else start


def schedule(days_by_city: list[tuple[date, str]], adults: int, children: int) -> list[VisitChoice] | None:
    """One attraction for each (day, city). None when some day cannot get one."""
    store = get_store()
    prefer_kids = children > 0

    def rank(a: Attraction) -> tuple:
        p = calculate_attraction_price(a.price_per_person, a.child_price, adults, children)
        return (p != 0, prefer_kids and not a.child_friendly, p, a.attraction_id)

    options: list[list[tuple[Attraction, datetime]]] = []
    for day, city in days_by_city:
        cands = []
        for a in sorted(store.get_attractions_in_city(city), key=rank):
            slot = _slot(a, day)
            if slot:
                cands.append((a, slot))
        options.append(cands)

    owner: dict[str, int] = {}           # attraction_id -> day index
    choice: dict[int, tuple[Attraction, datetime]] = {}

    def assign(i: int, seen: set[str]) -> bool:
        for a, slot in options[i]:
            if a.attraction_id in seen:
                continue
            seen.add(a.attraction_id)
            j = owner.get(a.attraction_id)
            if j is None or assign(j, seen):
                owner[a.attraction_id] = i
                choice[i] = (a, slot)
                return True
        return False

    for i in range(len(days_by_city)):
        if not assign(i, set()):
            return None
    return [VisitChoice(a, slot, calculate_attraction_price(a.price_per_person, a.child_price, adults, children))
            for a, slot in (choice[i] for i in range(len(days_by_city)))]

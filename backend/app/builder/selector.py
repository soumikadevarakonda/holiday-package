"""Choose one package by the city rule (T7), and the G4 alternatives."""

from __future__ import annotations

from app.builder.assemble import Parts
from app.builder.city_plans import target_city_count
from app.core.package_model import Package


def city_count_order(target: int, max_cities: int) -> list[int]:
    """c*, c*−1 … 1, then c*+1 … max."""
    return list(range(target, 0, -1)) + list(range(target + 1, max_cities + 1))


def choose(candidates: list[tuple[Parts, Package]], nights: int, cities_in_country: int, budget: int,
           min_per_city: int = 2) -> tuple[Parts, Package] | None:
    """Cheapest within budget at the first city count (in city-rule order) that has one. None = none fits."""
    if not candidates:
        return None
    target = target_city_count(nights, cities_in_country, min_per_city)
    max_cities = max(len(p.plan) for p, _ in candidates)
    for count in city_count_order(target, max(max_cities, target)):
        fitting = [(p, pkg) for p, pkg in candidates if len(p.plan) == count and pkg.total_inr <= budget]
        if fitting:
            return min(fitting, key=lambda c: (c[1].total_inr, _plan_key(c[0])))
    return None


def cheapest(candidates: list[tuple[Parts, Package]]) -> tuple[Parts, Package]:
    return min(candidates, key=lambda c: (c[1].total_inr, _plan_key(c[0])))


def alternatives(candidates: list[tuple[Parts, Package]], budget: int) -> dict[str, Package]:
    """G4 over the candidate packages (one per city plan, each assembled cheapest-first)."""
    if not candidates:
        return {}
    out = {"cheapest": cheapest(candidates)[1]}
    out["fastest"] = min(candidates, key=lambda c: (c[0].travel_minutes, c[1].total_inr, _plan_key(c[0])))[1]
    within = [c for c in candidates if c[1].total_inr <= budget] or candidates
    out["best_rated"] = max(within, key=lambda c: (c[0].avg_stars, -c[1].total_inr))[1]
    return out


def _plan_key(p: Parts) -> tuple:
    return tuple((c.city, c.nights) for c in p.plan)

"""Enumerate city plans: ordered distinct cities × night splits (each ≥ min nights), linked pairs only."""

from __future__ import annotations

from itertools import permutations

from app.core.package_model import CityStay


def compositions(total: int, parts: int, minimum: int) -> list[tuple[int, ...]]:
    """All ordered ways to split `total` into `parts` integers, each ≥ minimum."""
    if parts == 1:
        return [(total,)] if total >= minimum else []
    out = []
    for first in range(minimum, total - minimum * (parts - 1) + 1):
        out += [(first, *rest) for rest in compositions(total - first, parts - 1, minimum)]
    return out


def enumerate_plans(
    cities: list[str],
    nights: int,
    min_per_city: int,
    links: set[tuple[str, str]],
    first_ok: set[str] | None = None,
    last_ok: set[str] | None = None,
) -> list[list[CityStay]]:
    """Every valid plan. first_ok / last_ok: cities reachable from the arrival / return airports (None = any)."""
    plans: list[list[CityStay]] = []
    max_cities = min(len(cities), nights // min_per_city)
    for m in range(1, max_cities + 1):
        splits = compositions(nights, m, min_per_city)
        for order in permutations(sorted(cities), m):
            if first_ok is not None and order[0] not in first_ok:
                continue
            if last_ok is not None and order[-1] not in last_ok:
                continue
            if any((a, b) not in links for a, b in zip(order, order[1:])):
                continue
            plans += [[CityStay(c, n) for c, n in zip(order, split)] for split in splits]
    return plans


def target_city_count(nights: int, cities_in_country: int, min_per_city: int = 2) -> int:
    """City rule: c* = max(1, N // 3), capped by the country's cities and by N // min_per_city."""
    return max(1, min(nights // 3, cities_in_country, nights // min_per_city))

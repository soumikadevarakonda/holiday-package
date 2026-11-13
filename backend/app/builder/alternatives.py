"""G4: the three packages a traveler can pick from — cheapest, fastest and best rated.

Each city plan's package is first built cheapest-first. From there:
  * fastest    = per plan, swap to the shortest valid arrival / return flights, then take the plan with the least
                 total travel time (both flights + inter-city transfers); tie -> cheaper.
  * best rated = per plan, upgrade hotels (longest stay first) to the most stars that keep the package within
                 budget, then take the plan with the highest stars-per-night average; tie -> cheaper.
                 Guest `rating` does not count (problem statement, G4).
  * cheapest   = the lowest total over all plans.

Every swap goes through the same change code + validate() as a traveler's own change, so all three packages
respect every rule.
"""

from __future__ import annotations

from datetime import date

from app.catalog.store import get_store
from app.changes.options import options
from app.changes.side_effects import ChangeError, apply_change
from app.core.package_model import Change, Package
from app.rules.validator import validate


# ---------------------------------------------------------------- metrics
def travel_minutes(pkg: Package) -> int:
    """Both flights + every transfer between cities, in minutes."""
    store = get_store()
    total = 0
    for it in pkg.items:
        if it.type == "flight":
            f = store.get_flight(it.catalog_id)
            total += f.duration_minutes if f else 0
        elif it.type == "transfer":
            t = store.get_transfer(it.catalog_id)
            if t and t.from_city and t.to_city:
                total += t.duration_minutes
    return total


def _nights(it) -> int:
    return (date.fromisoformat(it.end[:10]) - date.fromisoformat(it.start[:10])).days


def avg_stars(pkg: Package) -> float:
    """Hotel stars averaged over the nights."""
    store = get_store()
    stays = [(store.get_hotel(it.catalog_id), _nights(it)) for it in pkg.items if it.type == "hotel" and it.end]
    nights = sum(n for _, n in stays)
    return sum((h.stars if h else 0) * n for h, n in stays) / nights if nights else 0.0


# ---------------------------------------------------------------- improving one plan
def _apply(pkg: Package, change: Change) -> Package | None:
    try:
        res = apply_change(pkg, change)
    except ChangeError:
        return None
    return None if validate(res.package) else res.package


def fastest_version(pkg: Package) -> Package:
    for leg in ("arrival", "return"):
        opts = options(pkg, "flight", leg=leg)
        if not opts:
            continue
        best = min(opts, key=lambda o: (o.details.get("duration_minutes", 10**6), o.price_diff, o.catalog_id))
        if not best.details.get("current"):
            pkg = _apply(pkg, Change(type="flight", leg=leg, flight_id=best.catalog_id)) or pkg
    return pkg


def best_rated_version(pkg: Package, budget: int) -> Package:
    hotels = sorted((it for it in pkg.items if it.type == "hotel"), key=lambda it: -_nights(it))
    for city in [h.city for h in hotels]:
        opts = [o for o in options(pkg, "hotel", city=city) if pkg.total_inr + o.price_diff <= budget]
        if not opts:
            continue
        best = max(opts, key=lambda o: (o.details.get("stars", 0), -o.price_diff, o.catalog_id))
        if not best.details.get("current"):
            pkg = _apply(pkg, Change(type="hotel", city=city, hotel_id=best.catalog_id, room_id=best.room_id)) or pkg
    return pkg


# ---------------------------------------------------------------- the three
def _plan_key(pkg: Package) -> tuple:
    return tuple((c.city, c.nights) for c in pkg.city_plan)


def three(packages: list[Package], budget: int) -> dict[str, Package]:
    """{"cheapest", "fastest", "best_rated"} over one package per city plan."""
    if not packages:
        return {}
    cheapest = min(packages, key=lambda p: (p.total_inr, _plan_key(p)))

    fast = [fastest_version(p) for p in packages]
    fastest = min(fast, key=lambda p: (travel_minutes(p), p.total_inr, _plan_key(p)))

    within = [p for p in packages if p.total_inr <= budget]
    if within:
        rated = [best_rated_version(p, budget) for p in within]
    else:  # nothing fits: show the highest-rated of the cheapest packages
        rated = packages
    best_rated = max(rated, key=lambda p: (avg_stars(p), -p.total_inr, _plan_key(p)))

    return {"cheapest": cheapest, "fastest": fastest, "best_rated": best_rated}

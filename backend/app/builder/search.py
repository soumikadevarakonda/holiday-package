"""Package search: enumerate city plans, fill each greedily, validate, choose by the city rule.  (Person A)

Signatures are frozen (Project.md section 3): build(req, mode, strategy) and rebuild(req, city_plan).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.builder import selector
from app.builder.assemble import Parts, assemble
from app.builder.attractions import schedule
from app.builder.city_plans import enumerate_plans
from app.builder.failures import Failures
from app.builder.flights import all_flights_on, arrival_flights, return_flights
from app.builder.hotels import StayOption, clear_cache, stay_options
from app.builder.transfers import TransferChoice, arrival_options, intercity_options, return_options
from app.catalog.models import Flight
from app.catalog.store import get_store
from app.core.money import format_inr
from app.core.package_model import BuildResult, CityPlanSummary, CityStay, Package, TripRequest
from app.rules.checks.dates import fmt
from app.rules.validator import validate


@dataclass
class _Request:
    req: TripRequest
    home_airport: str
    country: str
    cities: list[str]
    arrivals: list[Flight]
    returns: list[Flight]


# ------------------------------------------------------------------ request checks

def _prepare(req: TripRequest, fails: Failures) -> _Request | None:
    store = get_store()
    rules = store.rules
    country = store.get_country(req.country)
    home = store.indexes.departure_city_airports.get(req.departure_city)
    if country is None:
        fails.add("request", f"Unknown destination country '{req.country}'.")
        return None
    if home is None:
        fails.add("request", f"Unknown departure city '{req.departure_city}'.")
        return None
    if not rules.min_nights <= req.nights <= rules.max_nights:
        fails.add("request", f"Trips are {rules.min_nights} to {rules.max_nights} nights; {req.nights} requested.")
        return None
    first, last = date.fromisoformat(rules.first_night), date.fromisoformat(rules.last_departure)
    if req.start_date < first or req.end_date > last:
        fails.add("request", f"Flights run from {fmt(first)} to {fmt(last)}. A {req.nights}-night trip from "
                             f"{fmt(req.start_date)} returns on {fmt(req.end_date)}.")
        return None
    if req.travelers > store.max_flight_seats:
        fails.add("request", f"No flight has more than {store.max_flight_seats} seats left; "
                             f"{req.travelers} travelers must split into smaller groups.")
        return None
    cities = set(country.cities)
    arrivals = arrival_flights(home, cities, req.start_date, req.travelers)
    returns = return_flights(home, cities, req.end_date, req.travelers)
    n_arr, n_ret = all_flights_on(home, cities, req.start_date, req.end_date)
    if not arrivals:
        fails.add("flights", f"No flight from {home} lands in {country.name} on {fmt(req.start_date)}"
                  + (f" with {req.travelers} seats left ({n_arr} flight(s) are full)." if n_arr else "."))
        return None
    if not returns:
        fails.add("flights", f"No flight from {country.name} to {home} leaves on {fmt(req.end_date)}"
                  + (f" with {req.travelers} seats left ({n_ret} flight(s) are full)." if n_ret else "."))
        return None
    return _Request(req, home, country.name, sorted(cities), arrivals, returns)


# ------------------------------------------------------------------ one plan

def _serves(code: str, city: str) -> bool:
    ap = get_store().get_airport(code)
    return bool(ap and city in ap.serves_cities)


def _best_end(flights: list[Flight], stays: tuple[StayOption, ...], city: str, A: int, C: int, side: str):
    """Cheapest (flight + transfer) for each stay option at one end of the trip: {stay index: (cost, f, t)}."""
    best: dict[int, tuple[int, Flight, TransferChoice]] = {}
    for f in flights:
        if not _serves(f.to_airport if side == "arrival" else f.from_airport, city):
            continue
        f_cost = f.price_per_seat * (A + C)
        for i, s in enumerate(stays):
            opts = (arrival_options if side == "arrival" else return_options)(f, s.hotel, A, C)
            if opts and (i not in best or f_cost + opts[0].price < best[i][0]):
                best[i] = (f_cost + opts[0].price, f, opts[0])
    return best


def _brute_ends(r: _Request, plan: list[CityStay], stays_opts, A: int, C: int):
    """Oracle: try EVERY (arrival flight, transfer, first stay) × (return flight, transfer, last stay)
    combination, without the fast path's assumption that the two ends can be chosen separately."""
    first, last = plan[0].city, plan[-1].city
    arr = [(f.price_per_seat * (A + C) + t.price + s.price, i, f, t)
           for f in r.arrivals if _serves(f.to_airport, first)
           for i, s in enumerate(stays_opts[0]) for t in arrival_options(f, s.hotel, A, C)]
    ret = [(f.price_per_seat * (A + C) + t.price + (s.price if len(plan) > 1 else 0), j, f, t)
           for f in r.returns if _serves(f.from_airport, last)
           for j, s in enumerate(stays_opts[-1]) for t in return_options(f, s.hotel, A, C)]
    best = None
    for a in arr:
        for b in ret:
            if len(plan) == 1 and a[1] != b[1]:
                continue
            if best is None or a[0] + b[0] < best[0]:
                best = (a[0] + b[0], a, b)
    if best is None:
        return None
    _, a, b = best
    return a[1], (a[0], a[2], a[3]), b[1], (b[0], b[2], b[3])


def _build_plan(r: _Request, plan: list[CityStay], fails: Failures,
                strategy: str = "fast") -> tuple[Parts, Package] | None:
    req, A, C = r.req, r.req.adults, r.req.children
    check_ins, d = [], req.start_date
    for c in plan:
        check_ins.append(d)
        d += timedelta(days=c.nights)

    stays_opts = []
    for c, ci in zip(plan, check_ins):
        opts = stay_options(c.city, ci, c.nights, A, C)
        if not opts:
            fails.add("hotels", f"No hotel in {c.city} has rooms for {A} adult(s) and {C} child(ren) every night "
                                f"from {fmt(ci)} to {fmt(ci + timedelta(days=c.nights))}.")
            return None
        stays_opts.append(opts)

    first, last = plan[0].city, plan[-1].city
    arr = _best_end(r.arrivals, stays_opts[0], first, A, C, "arrival")
    if not arr:
        fails.add("arrival_transfer", f"No airport transfer reaches a {first} hotel in time after any flight "
                                      f"landing on {fmt(req.start_date)}.")
        return None
    ret = _best_end(r.returns, stays_opts[-1], last, A, C, "return")
    if not ret:
        fails.add("return_transfer", f"No airport transfer gets from a {last} hotel to the airport 3 hours before "
                                     f"any flight home on {fmt(req.end_date)}.")
        return None

    stays = [opts[0] for opts in stays_opts]
    if strategy == "brute":
        found = _brute_ends(r, plan, stays_opts, A, C)
        if found is None:
            fails.add("return_transfer", f"No combination of flights, transfers and hotels works for "
                                         f"{first} → {last}.")
            return None
        i, a_best, j, r_best = found
        stays[0], stays[-1] = stays_opts[0][i], stays_opts[-1][j]
    elif len(plan) == 1:
        both = [i for i in arr if i in ret]
        if not both:
            fails.add("return_transfer", f"No {first} hotel works with both the arrival and the return transfer.")
            return None
        i = min(both, key=lambda i: (stays_opts[0][i].price + arr[i][0] + ret[i][0], i))
        stays[0] = stays_opts[0][i]
        a_best, r_best = arr[i], ret[i]
    else:
        i = min(arr, key=lambda i: (stays_opts[0][i].price + arr[i][0], i))
        j = min(ret, key=lambda j: (stays_opts[-1][j].price + ret[j][0], j))
        stays[0], stays[-1] = stays_opts[0][i], stays_opts[-1][j]
        a_best, r_best = arr[i], ret[j]

    intercity = []
    for prev, nxt, ci in zip(plan, plan[1:], check_ins[1:]):
        opts = intercity_options(prev.city, nxt.city, ci, A, C)
        if not opts:
            fails.add("intercity", f"No transfer from {prev.city} to {nxt.city} runs on {fmt(ci)}.")
            return None
        intercity.append(opts[0])

    change_days = set(check_ins[1:])
    full_days = []
    for c, ci in zip(plan, check_ins):
        for n in range(c.nights):
            day = ci + timedelta(days=n)
            if day != req.start_date and day not in change_days:
                full_days.append((day, c.city))
    visits = schedule(full_days, A, C)
    if visits is None:
        fails.add("attractions", f"Not enough open attractions for one on every full day in "
                                 f"{' + '.join(f'{c.city} ({c.nights} nights)' for c in plan)}.")
        return None

    parts = Parts(plan, a_best[1], a_best[2], stays, intercity, visits, r_best[2], r_best[1])
    pkg = assemble(req, r.home_airport, r.country, parts)
    violations = validate(pkg, initial=True)
    if violations:
        fails.add("validation", f"Internal check failed ({violations[0].rule_id}): {violations[0].message}")
        return None
    return parts, pkg


def _plans(r: _Request) -> list[list[CityStay]]:
    store = get_store()
    links = {k for k, v in store.indexes.link_transfer_ids.items() if v}
    first_ok = {c for f in r.arrivals for c in store.get_airport(f.to_airport).serves_cities}
    last_ok = {c for f in r.returns for c in store.get_airport(f.from_airport).serves_cities}
    return enumerate_plans(r.cities, r.req.nights, store.rules.min_nights_per_city, links, first_ok, last_ok)


def _summaries(plans, results) -> list[CityPlanSummary]:
    out = []
    for plan, res in zip(plans, results):
        out.append(CityPlanSummary(plan=plan, total_inr=res[1].total_inr if res else None, valid=res is not None,
                                   reason=None if res else "No valid package for this plan."))
    return sorted(out, key=lambda s: (not s.valid, s.total_inr or 0, [(c.city, c.nights) for c in s.plan]))


# ------------------------------------------------------------------ public API

def build(req: TripRequest, mode: str = "default", strategy: str = "fast") -> BuildResult:
    """Build a package for a validated request.

    mode:     "default" = one package by the city rule; "three" = also fill `alternatives` (G4).
    strategy: "fast" (default) or "brute" (test oracle: no memoized hotel search).
    """
    if strategy == "brute":
        clear_cache()
    fails = Failures()
    r = _prepare(req, fails)
    if r is None:
        return BuildResult(outcome="NO_PACKAGE", reason=fails.best_reason())

    plans = _plans(r)
    results = [_build_plan(r, plan, fails, strategy) for plan in plans]
    candidates = [x for x in results if x]
    summaries = _summaries(plans, results)
    if not candidates:
        return BuildResult(outcome="NO_PACKAGE", city_plans=summaries,
                           reason=fails.best_reason() if plans else "No city plan fits the arrival and return airports.")

    store = get_store()
    n_cities = len(store.get_country(req.country).cities)
    alts = selector.alternatives(candidates, req.budget_inr) if mode == "three" else {}
    chosen = selector.choose(candidates, req.nights, n_cities, req.budget_inr, store.rules.min_nights_per_city)
    if chosen:
        return BuildResult(outcome="PACKAGE", package=chosen[1], alternatives=alts, city_plans=summaries)

    _, cheapest = selector.cheapest(candidates)
    over = cheapest.total_inr - req.budget_inr
    return BuildResult(outcome="OVER_BUDGET", package=cheapest, alternatives=alts, city_plans=summaries,
                       cheapest_total=cheapest.total_inr, over_by=over,
                       suggestion=_suggest(req, cheapest.total_inr))


def _suggest(req: TripRequest, cheapest_total: int) -> str:
    """M8: one concrete change. Prefer cutting a night if that fits; otherwise raise the budget."""
    rules = get_store().rules
    if req.nights > rules.min_nights:
        shorter = TripRequest(req.departure_city, req.country, req.start_date, req.nights - 1, req.adults,
                              req.children_ages, req.budget_inr, req.traveler_name)
        res = build(shorter)
        if res.outcome == "PACKAGE":
            return (f"Cut 1 night: {shorter.nights} nights costs {format_inr(res.package.total_inr)}, within your "
                    f"budget. Or raise the budget to {format_inr(cheapest_total)}.")
    return f"Raise the budget to {format_inr(cheapest_total)}."


def rebuild(req: TripRequest, city_plan: list[CityStay]) -> BuildResult:
    """Build on one given city plan (G3). Over budget is allowed (the UI warns); invalid plans are refused."""
    fails = Failures()
    r = _prepare(req, fails)
    if r is None:
        return BuildResult(outcome="NO_PACKAGE", reason=fails.best_reason())
    plan = [CityStay(c.city, c.nights) for c in city_plan]
    if plan not in _plans(r):
        return BuildResult(outcome="NO_PACKAGE", reason="That city plan is not valid for this request "
                           "(cities, order, nights, or airports).")
    res = _build_plan(r, plan, fails)
    if res is None:
        return BuildResult(outcome="NO_PACKAGE", reason=fails.best_reason())
    return BuildResult(outcome="PACKAGE", package=res[1],
                       city_plans=[CityPlanSummary(plan=plan, total_inr=res[1].total_inr, valid=True)])

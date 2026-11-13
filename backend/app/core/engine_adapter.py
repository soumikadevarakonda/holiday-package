"""Engine adapter: the ONE place where the API layer (Person B) meets the package engine (Person A).

The services work with plain dicts (what MySQL stores and the API returns); the engine works with the
dataclasses in core/package_model.py. This adapter converts in both directions:

    request form / Trip row  -> TripRequest          (build, rebuild)
    stored snapshot (dict)   <-> Package              (validate, options, apply_change, rebuild)
    PATCH body (dict)        -> Change                (apply_change)
    engine dataclasses       -> JSON-safe dicts       (BuildResult, CityPlanSummary, Option, Violation)
    ChangeError              -> 422 INVALID_CHANGE
    engine import failure    -> 503 ENGINE_UNAVAILABLE (only then; real engine errors are NOT hidden)

Tests can swap the adapter with set_engine_adapter().
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import date
from types import SimpleNamespace
from typing import Any

from app.core.errors import ConflictError, EngineUnavailableError, ValidationError
from app.core.package_model import Change, CityStay, Package, TripRequest

logger = logging.getLogger(__name__)

COUNTRY_ALIASES = {"uae": "United Arab Emirates", "u.a.e": "United Arab Emirates", "emirates": "United Arab Emirates",
                   "jp": "Japan", "ae": "United Arab Emirates"}


def _engine():
    """Import the engine lazily; only an import failure counts as 'engine unavailable'."""
    try:
        from app.builder import search
        from app.catalog.store import get_store
        from app.changes import options as options_mod
        from app.changes import side_effects
        from app.rules import validator
    except ImportError as exc:  # pragma: no cover - only when the engine is missing
        raise EngineUnavailableError("import", details={"error": str(exc)}) from exc
    return SimpleNamespace(search=search, validator=validator, options=options_mod,
                           side_effects=side_effects, get_store=get_store)


# ------------------------------------------------------------------ conversions

def _get(obj: Any, *names: str, default: Any = None) -> Any:
    for n in names:
        v = obj.get(n) if isinstance(obj, dict) else getattr(obj, n, None)
        if v is not None:
            return v
    return default


def _departure_city(value: str) -> str:
    """Accept a city name ('Bengaluru') or its airport code ('BLR')."""
    airports = _engine().get_store().indexes.departure_city_airports    # city -> airport
    if value in airports:
        return value
    by_code = {code: city for city, code in airports.items()}
    return by_code.get(value.upper(), value)


def _country(value: str) -> str:
    store = _engine().get_store()
    c = store.get_country(value) or store.get_country(COUNTRY_ALIASES.get(value.lower(), value))
    return c.name if c else value


def to_trip_request(req: Any) -> TripRequest:
    """Request schema / dict / Trip row -> TripRequest."""
    ages = _get(req, "children_ages", "child_ages", default=[]) or []
    start = _get(req, "start_date")
    if isinstance(start, str):
        start = date.fromisoformat(start[:10])
    return TripRequest(
        departure_city=_departure_city(str(_get(req, "departure_city", "origin"))),
        country=_country(str(_get(req, "country", "destination_country"))),
        start_date=start,
        nights=int(_get(req, "nights")),
        adults=int(_get(req, "adults")),
        children_ages=tuple(int(a) for a in ages),
        budget_inr=int(_get(req, "budget_inr", "budget", default=0)),
        traveler_name=str(_get(req, "traveler_name", default="Traveler")),
    )


def request_from_snapshot(snap: dict) -> TripRequest:
    """Rebuild the TripRequest from a stored package (for rebuild)."""
    t = snap["traveler"]
    start, end = date.fromisoformat(snap["start_date"]), date.fromisoformat(snap["end_date"])
    store = _engine().get_store()
    by_code = {code: city for city, code in store.indexes.departure_city_airports.items()}
    return TripRequest(by_code.get(t["home_airport"], t["home_airport"]), snap["country"], start,
                       (end - start).days, t["adults"], tuple(t.get("child_ages", [])),
                       int(snap.get("budget_inr", 0)), t.get("name", "Traveler"))


def to_package(snap: dict | Package) -> Package:
    if isinstance(snap, Package):
        return snap
    try:
        return Package.from_trip_format(snap)
    except (KeyError, TypeError) as exc:
        raise ValidationError(f"Stored package is not in the trip format: {exc}", code="INVALID_PACKAGE") from exc


def package_dict(pkg: Package | None) -> dict | None:
    return pkg.to_trip_format() if pkg is not None else None


def plan_dict(summary: Any) -> dict:
    """CityPlanSummary -> dict, with handy `cities` / `nights` / `label` fields for the UI."""
    d = asdict(summary)
    d["cities"] = [c["city"] for c in d["plan"]]
    d["nights"] = [c["nights"] for c in d["plan"]]
    d["label"] = " → ".join(f"{c['city']} ({c['nights']}N)" for c in d["plan"])
    return d


def to_city_plan(value: Any) -> list[CityStay]:
    """Accept {"plan": [{city, nights}]}, {"cities": [...], "nights": [...]} or a list of {city, nights}."""
    if isinstance(value, dict) and "plan" in value:
        value = value["plan"]
    elif isinstance(value, dict) and "cities" in value:
        value = [{"city": c, "nights": n} for c, n in zip(value["cities"], value.get("nights", []))]
    try:
        return [CityStay(str(c["city"]), int(c["nights"])) for c in value]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError("city_plan must be a list of {city, nights}.", code="INVALID_CITY_PLAN") from exc


def _result_ns(res: Any) -> SimpleNamespace:
    """BuildResult -> JSON-safe namespace (the service reads attributes)."""
    return SimpleNamespace(
        outcome=res.outcome,
        package=package_dict(res.package),
        city_plans=[plan_dict(s) for s in res.city_plans],
        alternatives={k: package_dict(v) for k, v in res.alternatives.items()},
        cheapest_total=res.cheapest_total,
        over_by=res.over_by,
        suggestion=res.suggestion,
        reason=res.reason,
    )


def to_change(pkg: Package, body: dict) -> list[Change]:
    """PATCH body -> Change(s). Accepts the PRD shape ({type, …}) and the flat shape
    ({kind, new_catalog_id, current_item_id, params}). An attraction swap becomes remove + add."""
    p = dict(body.get("params") or {})
    kind = body.get("type") or body.get("kind")
    new_id = body.get("new_catalog_id") or p.get("hotel_id") or p.get("flight_id") or p.get("attraction_id")
    item_id = body.get("current_item_id") or p.get("item_id")
    eng = _engine()

    if kind == "hotel":
        hotel = eng.get_store().get_hotel(new_id or "")
        city = p.get("city") or (hotel.city if hotel else None)
        room_id = p.get("room_id")
        if hotel and not room_id:   # pick the cheapest room type of that hotel that fits the travelers
            stay = next((h for h in pkg.items if h.type == "hotel" and h.city == city), None)
            if stay:
                from app.builder.hotels import stay_options
                ci, co = date.fromisoformat(stay.start), date.fromisoformat(stay.end)
                opts = [o for o in stay_options(city, ci, (co - ci).days, pkg.traveler.adults,
                                                len(pkg.traveler.child_ages)) if o.hotel.hotel_id == hotel.hotel_id]
                room_id = opts[0].room.room_id if opts else None
        return [Change(type="hotel", city=city, hotel_id=new_id, room_id=room_id)]
    if kind == "flight":
        leg = p.get("leg")
        if not leg:
            f = eng.get_store().get_flight(new_id or "")
            leg = "arrival" if f and f.from_airport == pkg.traveler.home_airport else "return"
        return [Change(type="flight", leg=leg, flight_id=new_id)]
    if kind in ("add_attraction", "remove_attraction"):
        return [Change(type=kind, item_id=item_id, attraction_id=new_id, date=p.get("date"), start=p.get("start"))]
    if kind == "attraction":
        if item_id and not new_id:
            return [Change(type="remove_attraction", item_id=item_id)]
        if item_id and new_id:      # swap: remove, then add on the same day
            old = next((i for i in pkg.items if i.item_id == item_id), None)
            day = p.get("date") or (old.start[:10] if old else None)
            return [Change(type="remove_attraction", item_id=item_id),
                    Change(type="add_attraction", attraction_id=new_id, date=day, start=p.get("start"))]
        return [Change(type="add_attraction", attraction_id=new_id, date=p.get("date"), start=p.get("start"))]
    raise ValidationError(f"Unknown change type '{kind}'. Use hotel, flight, add_attraction, remove_attraction "
                          "or attraction.", code="INVALID_CHANGE")


# ------------------------------------------------------------------ the adapter

class RealEngineAdapter:
    """Delegates to the package engine (app.builder / app.rules / app.changes / app.catalog)."""

    def is_engine_available(self) -> bool:
        try:
            _engine()
            return True
        except EngineUnavailableError:
            return False

    def build(self, req: Any, mode: str | None = None) -> SimpleNamespace:
        mode = mode or _get(req, "mode", default="default")
        return _result_ns(_engine().search.build(to_trip_request(req), mode=mode))

    def rebuild(self, req_or_snapshot: Any, city_plan: Any) -> SimpleNamespace:
        req = (request_from_snapshot(req_or_snapshot)
               if isinstance(req_or_snapshot, dict) and "traveler" in req_or_snapshot
               else to_trip_request(req_or_snapshot))
        res = _engine().search.rebuild(req, to_city_plan(city_plan))
        if res.outcome != "PACKAGE":
            raise ConflictError(res.reason or "That city plan has no valid package.", code="INVALID_CITY_PLAN")
        return _result_ns(res)

    def validate(self, pkg: Any, **kwargs: Any) -> list[dict]:
        """[] = valid; otherwise [{rule_id, item_ref, message}, …]."""
        from app.rules.violations import to_dicts
        return to_dicts(_engine().validator.validate(to_package(pkg), **kwargs))

    def options(self, pkg: Any, kind: str, **params: Any) -> list[dict]:
        eng = _engine()
        params = {k: v for k, v in params.items() if v is not None}
        try:
            return [asdict(o) for o in eng.options.options(to_package(pkg), kind, **params)]
        except KeyError as exc:
            need = {"hotel": "city", "flight": "leg", "attraction": "date"}.get(kind, str(exc))
            raise ValidationError(f"'{need}' is required for {kind} options.", code="INVALID_OPTION_QUERY") from exc
        except eng.side_effects.ChangeError as exc:
            raise ValidationError(str(exc), code="INVALID_OPTION_QUERY") from exc
        except ValueError as exc:   # e.g. a malformed date
            raise ValidationError(str(exc), code="INVALID_OPTION_QUERY") from exc

    def apply_change(self, pkg: Any, change: Any) -> SimpleNamespace:
        eng = _engine()
        current = to_package(pkg)
        changes = [change] if isinstance(change, Change) else to_change(current, dict(change))
        side_effects: list[str] = []
        warnings: list[str] = []
        try:
            for ch in changes:
                res = eng.side_effects.apply_change(current, ch)
                current = res.package
                side_effects += res.side_effects
                warnings += res.warnings
        except eng.side_effects.ChangeError as exc:
            raise ValidationError(str(exc), code="INVALID_CHANGE") from exc
        return SimpleNamespace(package=package_dict(current), side_effects=side_effects, warnings=warnings)

    def get_store(self) -> Any:
        return _engine().get_store()


_ACTIVE_ADAPTER: Any = RealEngineAdapter()


def get_engine_adapter() -> Any:
    return _ACTIVE_ADAPTER


def set_engine_adapter(adapter: Any) -> None:
    """Inject a custom adapter (test doubles)."""
    global _ACTIVE_ADAPTER
    _ACTIVE_ADAPTER = adapter


def reset_engine_adapter() -> None:
    global _ACTIVE_ADAPTER
    _ACTIVE_ADAPTER = RealEngineAdapter()

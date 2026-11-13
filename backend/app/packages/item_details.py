"""Read-only catalog details for package items, so the UI can show real airline / hotel / room / image data.

The stored package (and the export) keep the shared trip format unchanged; these details are added only to
API views (`details` on each item, `city` on each timeline day).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.catalog.store import get_store


def _nights(start: str | None, end: str | None) -> int | None:
    try:
        return (date.fromisoformat(str(end)[:10]) - date.fromisoformat(str(start)[:10])).days
    except (TypeError, ValueError):
        return None


def _flight(it: dict[str, Any], store, home: str | None) -> dict[str, Any]:
    f = store.get_flight(it.get("catalog_id", ""))
    if f is None:
        return {}
    dep, arr = store.get_airport(f.from_airport), store.get_airport(f.to_airport)
    return {
        "leg": "arrival" if home and f.from_airport == home else "return",
        "airline": f.airline, "flight_number": f.flight_number,
        "from_airport": f.from_airport, "to_airport": f.to_airport,
        "from_city": dep.city if dep else None, "to_city": arr.city if arr else None,
        "stops": f.stops, "duration_minutes": f.duration_minutes, "cabin": f.cabin,
    }


def _hotel(it: dict[str, Any], store) -> dict[str, Any]:
    h = store.get_hotel(it.get("catalog_id", ""))
    if h is None:
        return {}
    room = store.get_room(it.get("room_id") or "")
    out = {
        "hotel_name": h.name, "stars": h.stars, "rating": h.rating, "area": h.area, "image": h.image,
        "check_in_from": h.check_in_from, "check_out_until": h.check_out_until,
        "family_friendly": h.family_friendly, "nights": _nights(it.get("start"), it.get("end")),
    }
    if room is not None:
        out.update({"room_name": room.name, "room_type": room.room_type, "refundable": room.refundable})
    return out


def _transfer(it: dict[str, Any], store) -> dict[str, Any]:
    t = store.get_transfer(it.get("catalog_id", ""))
    if t is None:
        return {}
    return {
        "transfer_type": t.type, "from_point": t.from_point, "to_point": t.to_point,
        "duration_minutes": t.duration_minutes, "intercity": bool(t.from_city and t.to_city),
    }


def _attraction(it: dict[str, Any], store) -> dict[str, Any]:
    a = store.get_attraction(it.get("catalog_id", ""))
    if a is None:
        return {}
    return {
        "category": a.category, "image": a.image, "visit_minutes": a.visit_minutes,
        "open_from": a.open_from, "open_until": a.open_until, "child_friendly": a.child_friendly,
        "name_ja": a.name_ja,
    }


def with_details(items: list[dict[str, Any]], home_airport: str | None = None) -> list[dict[str, Any]]:
    """Copies of the items, each with a `details` dict taken from the catalog."""
    store = get_store()
    out = []
    for it in items:
        kind = it.get("type")
        try:
            if kind == "flight":
                details = _flight(it, store, home_airport)
            elif kind == "hotel":
                details = _hotel(it, store)
            elif kind == "transfer":
                details = _transfer(it, store)
            elif kind == "attraction":
                details = _attraction(it, store)
            else:
                details = {}
        except Exception:  # details are cosmetic; never break a response over them
            details = {}
        out.append({**it, "details": details})
    return out


def add_day_cities(timeline: list[dict[str, Any]], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each day gets the city of the hotel stayed in that night (the last city on the departure day)."""
    stays = sorted((str(it.get("start"))[:10], str(it.get("end"))[:10], it.get("city"))
                   for it in items if it.get("type") == "hotel" and it.get("start") and it.get("end"))
    for day in timeline:
        d = day.get("date", "")
        city = next((c for s, e, c in stays if s <= d < e), None)
        if city is None and stays:
            city = stays[-1][2] if d >= stays[-1][1] else stays[0][2]
        day["city"] = city
    return timeline

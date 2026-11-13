"""HTTP routes for the catalog module (GET /api/meta)."""

from typing import Any

from fastapi import APIRouter

from app.catalog.store import get_store

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/meta")
def get_meta() -> dict[str, Any]:
    """Return metadata needed by the frontend request form."""
    store = get_store()
    idx = store.indexes

    return {
        "departure_cities": [
            {"city": dc.city, "airport": dc.airport}
            for dc in idx.departure_cities
        ],
        "countries": [
            {"name": c.name, "code": c.code, "cities": c.cities}
            for c in idx.countries_by_name.values()
        ],
        "rules": {
            "min_nights": idx.rules_meta.min_nights,
            "max_nights": idx.rules_meta.max_nights,
            "min_nights_per_city": idx.rules_meta.min_nights_per_city,
            "data_window": {
                "first_night": idx.rules_meta.first_night,
                "last_departure": idx.rules_meta.last_departure,
            },
        },
        "max_flight_seats": store.max_flight_seats,
    }

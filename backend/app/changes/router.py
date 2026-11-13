"""
Changes router: component alternatives and change application.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.changes.apply import ChangesService
from app.core.database import get_db
from app.packages.schemas import ComponentChangeRequest

router = APIRouter(prefix="/api/packages", tags=["Package Changes"])


@router.get("/{package_id}/options/hotel")
def get_hotel_options(
    package_id: str = Path(..., description="Package identifier"),
    city: str | None = Query(default=None, description="Destination city name"),
    session: Session = Depends(get_db),
):
    """Retrieve alternative hotel options with price differences for a city stay."""
    service = ChangesService(session)
    return {
        "package_id": package_id,
        "kind": "hotel",
        "city": city,
        "options": service.get_options(package_id, "hotel", city=city),
    }


@router.get("/{package_id}/options/flight")
def get_flight_options(
    package_id: str = Path(..., description="Package identifier"),
    leg: str = Query(..., description="'arrival' (outbound) or 'return' (inbound)"),
    session: Session = Depends(get_db),
):
    """Retrieve alternative flight options with price differences for an arrival or return leg."""
    service = ChangesService(session)
    return {
        "package_id": package_id,
        "kind": "flight",
        "leg": leg,
        "options": service.get_options(package_id, "flight", leg=leg),
    }


@router.get("/{package_id}/options/attraction")
def get_attraction_options(
    package_id: str = Path(..., description="Package identifier"),
    date: str | None = Query(default=None, description="Visit date (YYYY-MM-DD)"),
    city: str | None = Query(default=None, description="City name"),
    session: Session = Depends(get_db),
):
    """Retrieve alternative attraction options with price differences for a specific day or city."""
    service = ChangesService(session)
    return {
        "package_id": package_id,
        "kind": "attraction",
        "date": date,
        "city": city,
        "options": service.get_options(package_id, "attraction", date=date, city=city),
    }


@router.patch("/{package_id}")
def apply_component_change(
    payload: ComponentChangeRequest,
    package_id: str = Path(..., description="Package identifier"),
    session: Session = Depends(get_db),
):
    """
    Apply a component change (hotel, flight, attraction):
    1. Evaluates change and side-effects via engine adapter.
    2. Re-validates the entire package.
    3. Rejects with 409 Conflict if rules are violated.
    4. Persists the modified package as a new version.
    """
    service = ChangesService(session)
    return service.apply_change(package_id, payload)

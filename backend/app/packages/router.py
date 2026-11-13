"""
Packages router: build, get, list, city-plans, rebuild, and undo.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.packages.schemas import PackageCreate, RebuildRequest
from backend.app.packages.service import PackageService

router = APIRouter(prefix="/api/packages", tags=["Packages"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_package(
    payload: PackageCreate,
    response: Response,
    session: Session = Depends(get_db),
):
    """
    Create a new package from request form inputs:
    1. Validates inputs against M1 constraints.
    2. Persists the trip request.
    3. Calls the package builder via the engine adapter.
    4. Persists the resulting package and returns its day-by-day itinerary.
    """
    service = PackageService(session)
    result = service.create_package(payload)
    if result.get("outcome") in ("OVER_BUDGET", "NO_PACKAGE"):
        response.status_code = status.HTTP_200_OK
    return result


@router.get("/{package_id}")
def get_package(
    package_id: str = Path(..., description="Package identifier"),
    session: Session = Depends(get_db),
):
    """
    Retrieve package details, current active version snapshot, and day-by-day plan.
    Does not rebuild on GET.
    """
    service = PackageService(session)
    return service.get_package(package_id)


@router.get("")
def list_packages(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = None,
    session: Session = Depends(get_db),
):
    """List persisted packages with pagination and status filter."""
    service = PackageService(session)
    return service.list_packages(limit=limit, offset=offset, status=status)


@router.get("/{package_id}/city-plans")
def get_package_city_plans(
    package_id: str = Path(..., description="Package identifier"),
    session: Session = Depends(get_db),
):
    """Retrieve alternative city plans for this package."""
    service = PackageService(session)
    return {
        "package_id": package_id,
        "city_plans": service.get_city_plans(package_id),
    }


@router.post("/{package_id}/rebuild")
def rebuild_package(
    payload: RebuildRequest,
    package_id: str = Path(..., description="Package identifier"),
    session: Session = Depends(get_db),
):
    """Rebuild a package using a selected alternative city plan."""
    service = PackageService(session)
    return service.rebuild_package(package_id, payload.city_plan)


@router.post("/{package_id}/undo")
def undo_package(
    package_id: str = Path(..., description="Package identifier"),
    session: Session = Depends(get_db),
):
    """Restore the previous package version under a new version number."""
    service = PackageService(session)
    return service.undo_package(package_id)

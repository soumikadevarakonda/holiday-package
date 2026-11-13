"""
Reservations router: confirmation and reservation lookup.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.packages.schemas import ConfirmPackageRequest
from backend.app.reservations.service import ReservationService

router = APIRouter(tags=["Reservations"])


@router.post("/api/packages/{package_id}/confirm", status_code=status.HTTP_201_CREATED)
def confirm_package(
    package_id: str = Path(..., description="Package identifier to confirm"),
    payload: Optional[ConfirmPackageRequest] = None,
    session: Session = Depends(get_db),
):
    """
    Confirm a holiday package booking:
    1. Validates the package against business rules via the engine adapter.
    2. Checks and allocates inventory (Feature S2).
    3. Issues a unique 10-digit numeric reservation reference.
    4. Freezes and persists an immutable snapshot of the package.
    """
    service = ReservationService(session)
    return service.confirm_package(package_id, request_data=payload)


@router.get("/api/reservations/{ref}")
def get_reservation(
    ref: str = Path(..., description="Exact 10-digit numeric reservation reference"),
    session: Session = Depends(get_db),
):
    """
    Look up a confirmed reservation by its 10-digit reference string.
    Returns 404 if not found or reference is invalid.
    """
    service = ReservationService(session)
    return service.get_reservation(ref)

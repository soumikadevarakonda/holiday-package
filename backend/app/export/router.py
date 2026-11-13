"""
Export router: downloadable JSON package export (Feature M5).
"""

from __future__ import annotations

import json
from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.engine_adapter import get_engine_adapter
from backend.app.core.errors import ConflictError, NotFoundError
from backend.app.export.trip_format import serialize_to_trip_format
from backend.app.packages.repository import PackageRepository
from backend.app.reservations.repository import ReservationRepository

router = APIRouter(prefix="/api/packages", tags=["Package Export"])


@router.get("/{package_id}/export")
def export_package(
    package_id: str = Path(..., description="Package identifier"),
    session: Session = Depends(get_db),
):
    """
    Export the package as a downloadable JSON file conforming to
    DATA_DICTIONARY.md section 4 shared trip format.
    """
    package_repo = PackageRepository(session)
    res_repo = ReservationRepository(session)
    engine_adapter = get_engine_adapter()

    package = package_repo.get_package(package_id)
    if package is None:
        raise NotFoundError(f"Package '{package_id}' not found")

    current_v = package.current_version
    if current_v is None:
        raise NotFoundError(f"No version snapshot found for package '{package_id}'")

    snapshot = dict(current_v.snapshot)

    # If engine adapter is connected and functional, validate package prior to export
    if engine_adapter.is_engine_available():
        violations = engine_adapter.validate(snapshot)
        if violations:
            raise ConflictError(
                message="Cannot export package: validation rules violated",
                code="RULE_VIOLATION",
                details={"violations": violations},
            )

    # Check for reservation booking reference
    reservation = res_repo.get_by_package_id(package_id)
    booking_ref = reservation.reference if (reservation and reservation.status == "CONFIRMED") else None

    # Serialize
    export_dict = serialize_to_trip_format(
        package_data=snapshot,
        trip_id=package.package_id,
        booking_reference=booking_ref,
        trip_request=package.trip,
    )

    json_content = json.dumps(export_dict, indent=2, ensure_ascii=False)
    filename = f"trip-{package_id}.json"

    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )

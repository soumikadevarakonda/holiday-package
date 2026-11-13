"""
Reservation service orchestrating validation, inventory allocation, and booking confirmation.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.core.engine_adapter import get_engine_adapter
from backend.app.core.errors import BadRequestError, ConflictError, NotFoundError
from backend.app.inventory.service import InventoryService
from backend.app.packages.repository import PackageRepository
from backend.app.packages.schemas import ConfirmPackageRequest
from backend.app.reservations.repository import ReservationRepository


class ReservationService:
    """Service handling booking confirmation and reservation lookups."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.package_repo = PackageRepository(session)
        self.reservation_repo = ReservationRepository(session)
        self.inventory_service = InventoryService(session)
        self.engine_adapter = get_engine_adapter()

    def confirm_package(
        self,
        package_id: str,
        request_data: Optional[ConfirmPackageRequest] = None,
    ) -> dict[str, Any]:
        """
        Confirm a package and issue a 10-digit reservation number.
        Executes inside an atomic transaction:
        1. Check base_version if specified.
        2. Validate package through engine adapter.
        3. Verify and allocate inventory.
        4. Issue 10-digit reference and persist immutable snapshot.
        5. Mark package status as 'BOOKED'.
        """
        package = self.package_repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")

        if package.status == "BOOKED":
            existing_res = self.reservation_repo.get_by_package_id(package_id)
            ref_str = existing_res.reference if existing_res else None
            raise ConflictError(
                f"Package '{package_id}' is already confirmed under reservation reference {ref_str}",
                code="ALREADY_BOOKED",
            )

        if (
            request_data is not None
            and request_data.base_version is not None
            and request_data.base_version != package.current_version_no
        ):
            raise ConflictError(
                message=f"Version conflict: current package version is {package.current_version_no}, but base_version was {request_data.base_version}",
                code="VERSION_CONFLICT",
            )

        current_v = package.current_version
        if current_v is None:
            raise NotFoundError(f"No version snapshot found for package '{package_id}'")

        snapshot = dict(current_v.snapshot)
        items = snapshot.get("items", [])

        # Step 1: Validate through engine adapter
        violations = self.engine_adapter.validate(snapshot)
        if violations:
            raise ConflictError(
                message="Cannot confirm package due to business rule violations",
                code="RULE_VIOLATION",
                details={"violations": violations},
            )

        # Step 2: Check and allocate inventory
        self.inventory_service.check_availability(items)

        # Total price
        total_price = package.total_price
        if total_price <= 0 and "total_inr" in snapshot:
            total_price = Decimal(str(snapshot["total_inr"]))

        # Step 3: Create reservation
        cust_name = request_data.customer_name if (request_data and request_data.customer_name) else "Guest Traveler"
        cust_email = request_data.customer_email if (request_data and request_data.customer_email) else "traveler@example.com"
        cust_phone = request_data.customer_phone if request_data else None

        snapshot["customer"] = {
            "name": cust_name,
            "email": cust_email,
            "phone": cust_phone,
        }

        reservation = self.reservation_repo.create_reservation(
            package_id=package.package_id,
            total_price=total_price,
            package_snapshot=snapshot,
            trip_id=package.trip_id,
        )

        # Step 4: Allocate inventory
        self.inventory_service.allocate_inventory(reservation.reservation_id, items)

        # Step 5: Mark package as booked
        package.status = "BOOKED"
        self.session.flush()

        return {
            "message": "Package confirmed successfully",
            "reservation": reservation.to_dict(),
            "reference": reservation.reference,
            "reservation_reference": reservation.reference,
            "status": "CONFIRMED",
            "customer_name": cust_name,
            "customer_email": cust_email,
            "items": items,
        }

    def get_reservation(self, reference: str) -> dict[str, Any]:
        """
        Retrieve a confirmed reservation by 10-digit reference number.
        Returns 400 if not 10 digits, or 404 NotFoundError if not found.
        """
        clean_ref = reference.strip()
        if len(clean_ref) != 10 or not clean_ref.isdigit():
            raise BadRequestError("Reservation reference must be exactly 10 digits", code="INVALID_REFERENCE")

        reservation = self.reservation_repo.get_by_reference(clean_ref)
        if reservation is None:
            raise NotFoundError(f"Reservation '{clean_ref}' not found")

        snap = reservation.package_snapshot or {}
        cust = snap.get("customer", {})
        return {
            "reservation_id": reservation.reservation_id,
            "reference": reservation.reference,
            "reservation_reference": reservation.reference,
            "package_id": reservation.package_id,
            "status": reservation.status,
            "customer_name": cust.get("name", "Guest Traveler"),
            "customer_email": cust.get("email", "traveler@example.com"),
            "total_price": float(reservation.total_price),
            "created_at": reservation.created_at.isoformat() if reservation.created_at else None,
            "items": [it.to_dict() for it in reservation.items] if reservation.items else snap.get("items", []),
            "snapshot": snap,
        }

        return {
            "reservation_id": reservation.reservation_id,
            "reference": reservation.reference,
            "package_id": reservation.package_id,
            "status": reservation.status,
            "total_price": float(reservation.total_price),
            "created_at": reservation.created_at.isoformat() if reservation.created_at else None,
            "snapshot": reservation.package_snapshot or {},
        }

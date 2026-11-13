"""
Reservation service orchestrating validation, inventory allocation, and booking confirmation.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.engine_adapter import get_engine_adapter
from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.inventory.service import InventoryService
from app.packages.item_details import with_details
from app.packages.repository import PackageRepository
from app.packages.schemas import ConfirmPackageRequest
from app.reservations.repository import ReservationRepository


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
            # Idempotent (PRD edge case "double-click Confirm"): return the existing reservation.
            existing_res = self.reservation_repo.get_by_package_id(package_id)
            if existing_res is not None:
                result = self.get_reservation(existing_res.reference)
                result.update({"message": "Package was already confirmed", "already_confirmed": True})
                return result
            raise ConflictError(f"Package '{package_id}' is booked but has no reservation", code="ALREADY_BOOKED")

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

        # Freeze the snapshot as BOOKED with the reference (M7: export shows status BOOKED + booking.reference)
        booked = dict(snapshot)
        booked["items"] = [{**it, "status": "BOOKED", "booking": {"reference": reservation.reference}}
                           for it in items]
        reservation.package_snapshot = booked

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
            "package_id": package.package_id,
            "customer_name": cust_name,
            "customer_email": cust_email,
            "total_inr": int(total_price),
            "items": booked["items"],
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
            raise NotFoundError("Reservation not found", details={"reference": clean_ref})

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
            "items": with_details(snap.get("items", []), (snap.get("traveler") or {}).get("home_airport")),
            "total_inr": int(reservation.total_price),
            "snapshot": snap,
        }

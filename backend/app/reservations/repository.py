"""
Reservation repository for persisting confirmed bookings and snapshots.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.reservations.reference import generate_reservation_reference
from app.models.reservation import Reservation, ReservationItem


class ReservationRepository:
    """Data access repository for reservations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_reservation(
        self,
        package_id: str,
        total_price: Decimal,
        package_snapshot: dict[str, Any],
        custom_reference: Optional[str] = None,
        trip_id: Optional[str] = None,
    ) -> Reservation:
        """
        Create a reservation with unique 10-digit reference, retrying on collision.
        """
        max_attempts = 10
        for attempt in range(max_attempts):
            ref = custom_reference if (custom_reference and attempt == 0) else generate_reservation_reference()

            # Ensure reference doesn't already exist
            if self.get_by_reference(ref) is not None:
                continue

            reservation = Reservation(
                package_id=package_id,
                trip_id=trip_id,
                reference=ref,
                status="CONFIRMED",
                total_price=total_price,
                package_snapshot=package_snapshot,
            )

            # Also create legacy reservation_items if items list is present
            for it in package_snapshot.get("items", []):
                reservation.items.append(
                    ReservationItem(
                        item_type=it.get("type") or it.get("item_type", "unknown"),
                        catalogue_id=it.get("catalog_id") or it.get("catalogue_id", ""),
                        item_snapshot=it,
                        price=Decimal(str(it.get("price_inr") or it.get("price", 0))),
                        quantity=int(it.get("quantity", 1)),
                    )
                )

            try:
                self.session.add(reservation)
                self.session.flush()
                return reservation
            except IntegrityError:
                self.session.rollback()
                if attempt == max_attempts - 1:
                    raise

        raise RuntimeError("Failed to generate unique 10-digit reservation reference after multiple retries")

    def get_by_id(self, reservation_id: str) -> Optional[Reservation]:
        """Retrieve reservation by primary key."""
        return self.session.get(Reservation, reservation_id)

    def get_by_reference(self, reference: str) -> Optional[Reservation]:
        """Retrieve reservation by exact 10-digit reference string."""
        stmt = select(Reservation).where(Reservation.reference == reference)
        return self.session.scalars(stmt).first()

    def get_by_package_id(self, package_id: str) -> Optional[Reservation]:
        """Retrieve reservation for a package."""
        stmt = select(Reservation).where(Reservation.package_id == package_id)
        return self.session.scalars(stmt).first()

    def cancel_reservation(self, reference: str) -> Optional[Reservation]:
        """Cancel reservation by reference."""
        res = self.get_by_reference(reference)
        if res:
            res.status = "CANCELLED"
            self.session.flush()
        return res

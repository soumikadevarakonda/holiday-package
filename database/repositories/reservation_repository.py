"""
Reservation repository for persisting and querying Reservations and ReservationItems.
"""

from __future__ import annotations

import secrets
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models.reservation import Reservation, ReservationItem
from database.models.trip import Trip


class ReservationRepository:
    """
    Data access repository for Reservations with collision-safe 10-digit reference generation.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def generate_reference(self) -> str:
        """
        Generate a cryptographically secure 10-digit numeric reference.
        Range: 1000000000 to 9999999999.
        """
        # Ensure exact 10-digit numeric string (leading digit 1-9)
        return str(secrets.randbelow(9000000000) + 1000000000)

    def create_reservation(self, reservation: Reservation) -> Reservation:
        """
        Persist a reservation entity.
        If reference is not provided, automatically generates a unique 10-digit reference,
        retrying on collision.
        """
        max_attempts = 10
        for attempt in range(max_attempts):
            if not reservation.reference or attempt > 0:
                reservation.reference = self.generate_reference()

            # Verify no existing reservation with this reference
            existing = self.get_by_reference(reservation.reference)
            if existing is not None:
                continue

            try:
                self.session.add(reservation)
                self.session.flush()
                return reservation
            except IntegrityError:
                self.session.rollback()
                if attempt == max_attempts - 1:
                    raise

        raise RuntimeError("Failed to generate a unique 10-digit reference after multiple attempts")

    def create_reservation_from_trip(
        self,
        trip: Trip,
        status: str = "CONFIRMED",
    ) -> Reservation:
        """
        Create a confirmed reservation from a Trip entity.
        Takes immutable snapshots of all current trip items and stores them.
        Also transitions trip status to 'BOOKED'.
        """
        total_price = trip.total_price

        reservation = Reservation(
            trip_id=trip.trip_id,
            reference=self.generate_reference(),
            status=status,
            total_price=total_price,
        )

        for item in trip.items:
            snapshot = {
                "item_id": item.item_id,
                "item_type": item.item_type,
                "catalogue_id": item.catalogue_id,
                "city_name": item.city_name,
                "start_datetime": item.start_datetime.isoformat() if item.start_datetime else None,
                "end_datetime": item.end_datetime.isoformat() if item.end_datetime else None,
                "price": float(item.price),
                "quantity": item.quantity,
                "item_details": item.item_details or {},
            }

            reservation.items.append(
                ReservationItem(
                    item_type=item.item_type,
                    catalogue_id=item.catalogue_id,
                    item_snapshot=snapshot,
                    price=item.price,
                    quantity=item.quantity,
                )
            )

        persisted = self.create_reservation(reservation)
        trip.status = "BOOKED"
        self.session.flush()
        return persisted

    def get_by_id(self, reservation_id: str) -> Optional[Reservation]:
        """Retrieve a reservation by primary key reservation_id."""
        stmt = select(Reservation).where(Reservation.reservation_id == reservation_id)
        return self.session.scalars(stmt).first()

    def get_by_reference(self, reference: str) -> Optional[Reservation]:
        """
        Retrieve a reservation by exact 10-digit reference string.
        Returns None if not found (used by /reservation/:ref summary endpoint).
        """
        stmt = select(Reservation).where(Reservation.reference == reference)
        return self.session.scalars(stmt).first()

    def list_by_trip(self, trip_id: str) -> list[Reservation]:
        """List all reservations associated with a trip_id."""
        stmt = (
            select(Reservation)
            .where(Reservation.trip_id == trip_id)
            .order_by(Reservation.created_at.desc())
        )
        return list(self.session.scalars(stmt).all())

    def update_status(self, reservation_id: str, new_status: str) -> Optional[Reservation]:
        """Update reservation status (e.g. CONFIRMED -> CANCELLED)."""
        reservation = self.get_by_id(reservation_id)
        if reservation:
            reservation.status = new_status
            self.session.flush()
        return reservation

    def cancel_reservation(self, reference: str) -> Optional[Reservation]:
        """Cancel a reservation by reference."""
        reservation = self.get_by_reference(reference)
        if reservation:
            reservation.status = "CANCELLED"
            self.session.flush()
        return reservation

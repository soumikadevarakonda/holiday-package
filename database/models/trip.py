"""
Trip ORM model.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from database.models import Base

if TYPE_CHECKING:
    from database.models.reservation import Reservation
    from database.models.trip_city import TripCity
    from database.models.trip_item import TripItem


class Trip(Base):
    """
    User-initiated holiday trip request and its generated package state.
    """

    __tablename__ = "trips"

    trip_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"trip-{uuid.uuid4().hex[:12]}",
    )
    departure_city: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_country: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    nights: Mapped[int] = mapped_column(Integer, nullable=False)
    adults: Mapped[int] = mapped_column(Integer, nullable=False)
    children: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    child_ages: Mapped[Optional[list[int]]] = mapped_column(JSON, nullable=True)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    cities: Mapped[list["TripCity"]] = relationship(
        "TripCity",
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="TripCity.sequence_order",
        lazy="selectin",
    )
    items: Mapped[list["TripItem"]] = relationship(
        "TripItem",
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="TripItem.start_datetime",
        lazy="selectin",
    )
    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation",
        back_populates="trip",
        cascade="all",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("nights >= 1 AND nights <= 30", name="chk_trips_nights"),
        CheckConstraint("adults >= 1", name="chk_trips_adults"),
        CheckConstraint("children >= 0", name="chk_trips_children"),
        CheckConstraint("budget >= 0.00", name="chk_trips_budget"),
        Index("idx_trips_status", "status"),
        Index("idx_trips_start_date", "start_date"),
    )

    @property
    def total_price(self) -> Decimal:
        """Sum of price across all items."""
        return sum((item.price for item in self.items), Decimal("0.00"))

    def to_dict(self) -> dict[str, Any]:
        """Convert Trip to standard dictionary."""
        return {
            "trip_id": self.trip_id,
            "departure_city": self.departure_city,
            "destination_country": self.destination_country,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "nights": self.nights,
            "adults": self.adults,
            "children": self.children,
            "child_ages": self.child_ages or [],
            "budget": float(self.budget) if self.budget is not None else 0.0,
            "total_price": float(self.total_price),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "cities": [c.to_dict() for c in self.cities],
            "items": [i.to_dict() for i in self.items],
        }

    def to_export_format(self, traveler_name: str = "Traveler") -> dict[str, Any]:
        """
        Convert to the shared trip format (Problem 1 Section 4 specification).
        """
        from datetime import timedelta

        end_date = self.start_date + timedelta(days=self.nights) if self.start_date else None

        # Check for confirmed booking reference
        latest_res = self.reservations[-1] if self.reservations else None
        booking_ref = latest_res.reference if (latest_res and latest_res.status == "CONFIRMED") else None

        return {
            "trip_id": self.trip_id,
            "traveler": {
                "name": traveler_name,
                "home_airport": None,  # Can be populated from catalogue departure city lookup
                "adults": self.adults,
                "children": self.children,
                "child_ages": self.child_ages or [],
            },
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "country": self.destination_country,
            "budget_inr": int(self.budget),
            "total_inr": int(self.total_price),
            "items": [
                item.to_export_format(booking_reference=booking_ref)
                for item in self.items
            ],
        }

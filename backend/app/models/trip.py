"""Trip ORM model: the validated request as entered (M1)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import CheckConstraint, Date, DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models import Base

if TYPE_CHECKING:
    from app.models.reservation import Reservation


class Trip(Base):
    """User-initiated holiday trip request."""

    __tablename__ = "trips"

    trip_id: Mapped[str] = mapped_column(String(64), primary_key=True,
                                         default=lambda: f"trip-{uuid.uuid4().hex[:12]}")
    departure_city: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_country: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    nights: Mapped[int] = mapped_column(Integer, nullable=False)
    adults: Mapped[int] = mapped_column(Integer, nullable=False)
    children: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    child_ages: Mapped[Optional[list[int]]] = mapped_column(JSON, nullable=True)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    traveler_name: Mapped[str] = mapped_column(String(100), nullable=False, default="Traveler")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(),
                                                 onupdate=func.now())

    reservations: Mapped[list["Reservation"]] = relationship("Reservation", back_populates="trip",
                                                              cascade="all", lazy="selectin")

    __table_args__ = (
        CheckConstraint("nights >= 1 AND nights <= 30", name="chk_trips_nights"),
        CheckConstraint("adults >= 1", name="chk_trips_adults"),
        CheckConstraint("children >= 0", name="chk_trips_children"),
        CheckConstraint("budget >= 0.00", name="chk_trips_budget"),
        Index("idx_trips_status", "status"),
        Index("idx_trips_start_date", "start_date"),
    )

    def to_dict(self) -> dict[str, Any]:
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
            "traveler_name": self.traveler_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

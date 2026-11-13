"""
TripItem ORM model.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from database.models import Base

if TYPE_CHECKING:
    from database.models.trip import Trip


class TripItem(Base):
    """
    An individual travel service line-item within a package.
    References the immutable JSON catalogue record via catalogue_id.
    """

    __tablename__ = "trip_items"

    item_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"item-{uuid.uuid4().hex[:12]}",
    )
    trip_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("trips.trip_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    catalogue_id: Mapped[str] = mapped_column(String(64), nullable=False)
    city_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    item_details: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="items")

    __table_args__ = (
        CheckConstraint(
            "item_type IN ('flight', 'hotel', 'transfer', 'attraction')",
            name="chk_trip_items_type",
        ),
        CheckConstraint("price >= 0.00", name="chk_trip_items_price"),
        CheckConstraint("quantity >= 1", name="chk_trip_items_quantity"),
        Index("idx_trip_items_trip_id", "trip_id"),
        Index("idx_trip_items_type", "item_type"),
        Index("idx_trip_items_catalogue_id", "catalogue_id"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert TripItem to dictionary."""
        return {
            "item_id": self.item_id,
            "trip_id": self.trip_id,
            "item_type": self.item_type,
            "catalogue_id": self.catalogue_id,
            "city_name": self.city_name,
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
            "price": float(self.price),
            "quantity": self.quantity,
            "item_details": self.item_details or {},
        }

    def to_export_format(
        self, booking_reference: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Convert to shared trip format specification (Problem 1 Section 4).
        """
        details = self.item_details or {}
        name = details.get("name", f"{self.item_type.capitalize()} {self.catalogue_id}")
        room_id = details.get("room_id") if self.item_type == "hotel" else None
        status = "BOOKED" if booking_reference else details.get("status", "PLANNED")

        # Format start and end date/time strings
        # Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM
        if self.item_type == "hotel":
            start_str = self.start_datetime.strftime("%Y-%m-%d") if self.start_datetime else None
            end_str = self.end_datetime.strftime("%Y-%m-%d") if self.end_datetime else None
        else:
            start_str = self.start_datetime.strftime("%Y-%m-%dT%H:%M") if self.start_datetime else None
            end_str = self.end_datetime.strftime("%Y-%m-%dT%H:%M") if self.end_datetime else None

        booking_obj = {"reference": booking_reference} if booking_reference else None

        return {
            "item_id": self.item_id,
            "type": self.item_type,
            "name": name,
            "city": self.city_name,
            "status": status,
            "catalog_id": self.catalogue_id,
            "room_id": room_id,
            "start": start_str,
            "end": end_str,
            "quantity": self.quantity,
            "price_inr": int(self.price),
            "booking": booking_obj,
            "sources": [],
            "warnings": details.get("warnings", []),
        }

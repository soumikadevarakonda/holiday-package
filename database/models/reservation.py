"""
Reservation and ReservationItem ORM models.
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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from database.models import Base

if TYPE_CHECKING:
    from database.models.trip import Trip


class Reservation(Base):
    """
    Confirmed booking reservation identified by an exact 10-digit numeric reference.
    """

    __tablename__ = "reservations"

    reservation_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"res-{uuid.uuid4().hex[:12]}",
    )
    trip_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("trips.trip_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("packages.package_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
    )
    reference: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="CONFIRMED",
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    package_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="reservations")
    items: Mapped[list["ReservationItem"]] = relationship(
        "ReservationItem",
        back_populates="reservation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "length(reference) = 10",
            name="chk_reservations_reference_len",
        ),
        CheckConstraint("total_price >= 0.00", name="chk_reservations_total_price"),
        Index("idx_reservations_trip_id", "trip_id"),
        Index("idx_reservations_status", "status"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert Reservation to dictionary."""
        return {
            "reservation_id": self.reservation_id,
            "trip_id": self.trip_id,
            "package_id": self.package_id,
            "reference": self.reference,
            "status": self.status,
            "total_price": float(self.total_price),
            "package_snapshot": self.package_snapshot or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items": [item.to_dict() for item in self.items],
        }


class ReservationItem(Base):
    """
    Frozen snapshot of a booked travel service item at confirmation time.
    """

    __tablename__ = "reservation_items"

    reservation_item_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"ri-{uuid.uuid4().hex[:12]}",
    )
    reservation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey(
            "reservations.reservation_id", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    catalogue_id: Mapped[str] = mapped_column(String(64), nullable=False)
    item_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    reservation: Mapped["Reservation"] = relationship(
        "Reservation", back_populates="items"
    )

    __table_args__ = (
        CheckConstraint("price >= 0.00", name="chk_res_items_price"),
        CheckConstraint("quantity >= 1", name="chk_res_items_quantity"),
        Index("idx_res_items_reservation_id", "reservation_id"),
        Index("idx_res_items_catalogue_id", "catalogue_id"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert ReservationItem to dictionary."""
        return {
            "reservation_item_id": self.reservation_item_id,
            "reservation_id": self.reservation_id,
            "item_type": self.item_type,
            "catalogue_id": self.catalogue_id,
            "item_snapshot": self.item_snapshot,
            "price": float(self.price),
            "quantity": self.quantity,
        }

"""
InventoryUsage ORM model for tracking consumed seats and rooms (Feature S2).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models import Base

if TYPE_CHECKING:
    from database.models.reservation import Reservation


class InventoryUsage(Base):
    """
    Tracks inventory consumed by confirmed bookings.
    Ensures that seats on flights and rooms on specific dates are not overbooked.
    """

    __tablename__ = "inventory_usage"

    usage_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"inv-{uuid.uuid4().hex[:12]}",
    )
    reservation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("reservations.reservation_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    item_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    catalogue_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    allocated_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    reservation: Mapped["Reservation"] = relationship("Reservation")

    __table_args__ = (
        CheckConstraint("item_type IN ('flight', 'room')", name="chk_inv_usage_type"),
        CheckConstraint("quantity >= 1", name="chk_inv_usage_quantity"),
        Index("idx_inv_usage_res_id", "reservation_id"),
        Index("idx_inv_usage_item_date", "item_type", "catalogue_id", "allocated_date"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert InventoryUsage to dictionary."""
        return {
            "usage_id": self.usage_id,
            "reservation_id": self.reservation_id,
            "item_type": self.item_type,
            "catalogue_id": self.catalogue_id,
            "allocated_date": self.allocated_date.isoformat() if self.allocated_date else None,
            "quantity": self.quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

"""
Inventory repository for managing consumed seats and room allocations.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryUsage


class InventoryRepository:
    """Repository for querying and recording inventory usage."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record_usage(
        self,
        reservation_id: str,
        item_type: str,
        catalogue_id: str,
        allocated_date: date,
        quantity: int,
    ) -> InventoryUsage:
        """Add an inventory allocation record."""
        usage = InventoryUsage(
            reservation_id=reservation_id,
            item_type=item_type,
            catalogue_id=catalogue_id,
            allocated_date=allocated_date,
            quantity=quantity,
        )
        self.session.add(usage)
        self.session.flush()
        return usage

    def get_allocated_quantity(
        self,
        item_type: str,
        catalogue_id: str,
        allocated_date: date,
    ) -> int:
        """Sum total allocated seats or rooms for an item on a date."""
        stmt = (
            select(func.coalesce(func.sum(InventoryUsage.quantity), 0))
            .where(
                InventoryUsage.item_type == item_type,
                InventoryUsage.catalogue_id == catalogue_id,
                InventoryUsage.allocated_date == allocated_date,
            )
        )
        return int(self.session.scalar(stmt) or 0)

    def list_by_reservation(self, reservation_id: str) -> list[InventoryUsage]:
        """List all inventory records associated with a reservation."""
        stmt = select(InventoryUsage).where(InventoryUsage.reservation_id == reservation_id)
        return list(self.session.scalars(stmt).all())

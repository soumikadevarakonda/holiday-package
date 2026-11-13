"""
Inventory service for verifying and allocating seats and rooms on booking confirmation (Feature S2).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.errors import ConflictError
from backend.app.inventory.repository import InventoryRepository
from database.catalog_loader import get_catalog


class InventoryService:
    """Service to track effective inventory (catalog capacity minus booked allocations)."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = InventoryRepository(session)
        self.catalog = get_catalog()

    def check_availability(self, items: list[dict[str, Any]]) -> None:
        """
        Verify that all flights and hotel rooms in the package have sufficient remaining inventory.
        Raises ConflictError if any item is depleted.
        """
        for item in items:
            item_type = item.get("type") or item.get("item_type")
            cat_id = item.get("catalog_id") or item.get("catalogue_id")
            quantity = int(item.get("quantity", 1))

            if item_type == "flight":
                flight = self.catalog.indexes.get_flight(cat_id)
                if flight is None:
                    continue

                catalog_seats = int(flight.get("seats_left", 9))
                # Flight date from departure_local or start
                start_raw = item.get("start") or item.get("start_datetime")
                fl_date = date.fromisoformat(str(start_raw)[:10])

                already_booked = self.repo.get_allocated_quantity(
                    item_type="flight",
                    catalogue_id=cat_id,
                    allocated_date=fl_date,
                )
                if already_booked + quantity > catalog_seats:
                    raise ConflictError(
                        f"Flight {cat_id} has insufficient seats: requested {quantity}, "
                        f"remaining {catalog_seats - already_booked}"
                    )

            elif item_type == "hotel":
                room_id = item.get("room_id")
                if not room_id:
                    continue

                # Room nights from start to end
                start_raw = item.get("start") or item.get("start_datetime")
                end_raw = item.get("end") or item.get("end_datetime")
                if not start_raw or not end_raw:
                    continue

                start_d = date.fromisoformat(str(start_raw)[:10])
                end_d = date.fromisoformat(str(end_raw)[:10])

                curr = start_d
                from datetime import timedelta
                while curr < end_d:
                    dt_str = curr.isoformat()
                    catalog_rooms = self.catalog.indexes.get_rooms_left(room_id, dt_str)
                    if catalog_rooms is not None:
                        already_booked = self.repo.get_allocated_quantity(
                            item_type="room",
                            catalogue_id=room_id,
                            allocated_date=curr,
                        )
                        if already_booked + quantity > catalog_rooms:
                            raise ConflictError(
                                f"Room {room_id} has insufficient availability on {dt_str}: "
                                f"requested {quantity}, remaining {catalog_rooms - already_booked}"
                            )
                    curr += timedelta(days=1)

    def allocate_inventory(self, reservation_id: str, items: list[dict[str, Any]]) -> None:
        """
        Allocate inventory seats and rooms inside the confirmation transaction.
        """
        for item in items:
            item_type = item.get("type") or item.get("item_type")
            cat_id = item.get("catalog_id") or item.get("catalogue_id")
            quantity = int(item.get("quantity", 1))

            if item_type == "flight":
                start_raw = item.get("start") or item.get("start_datetime")
                fl_date = date.fromisoformat(str(start_raw)[:10])
                self.repo.record_usage(
                    reservation_id=reservation_id,
                    item_type="flight",
                    catalogue_id=cat_id,
                    allocated_date=fl_date,
                    quantity=quantity,
                )
            elif item_type == "hotel":
                room_id = item.get("room_id")
                if not room_id:
                    continue

                start_raw = item.get("start") or item.get("start_datetime")
                end_raw = item.get("end") or item.get("end_datetime")
                if not start_raw or not end_raw:
                    continue

                start_d = date.fromisoformat(str(start_raw)[:10])
                end_d = date.fromisoformat(str(end_raw)[:10])

                curr = start_d
                from datetime import timedelta
                while curr < end_d:
                    self.repo.record_usage(
                        reservation_id=reservation_id,
                        item_type="room",
                        catalogue_id=room_id,
                        allocated_date=curr,
                        quantity=quantity,
                    )
                    curr += timedelta(days=1)

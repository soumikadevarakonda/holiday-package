"""
Trip repository for persisting and querying Trips, TripCities, and TripItems.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from database.models.trip import Trip
from database.models.trip_city import TripCity
from database.models.trip_item import TripItem


class TripRepository:
    """
    Data access repository for application Trips and associated entities.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_trip(self, trip: Trip) -> Trip:
        """Add and persist a new Trip entity with its cities and items."""
        self.session.add(trip)
        self.session.flush()
        return trip

    def get_trip_by_id(self, trip_id: str) -> Optional[Trip]:
        """Retrieve a trip by its unique trip_id."""
        stmt = select(Trip).where(Trip.trip_id == trip_id)
        return self.session.scalars(stmt).first()

    def update_trip_status(self, trip_id: str, new_status: str) -> Optional[Trip]:
        """Update status of a trip (e.g. DRAFT -> PLANNED -> BOOKED)."""
        trip = self.get_trip_by_id(trip_id)
        if trip:
            trip.status = new_status
            self.session.flush()
        return trip

    def save_trip(self, trip: Trip) -> Trip:
        """
        Create or update a Trip.
        If existing, merges attributes, replaces or updates cities and items.
        """
        existing = self.get_trip_by_id(trip.trip_id)
        if existing is None:
            self.session.add(trip)
            self.session.flush()
            return trip

        # Update existing record scalar fields
        existing.departure_city = trip.departure_city
        existing.destination_country = trip.destination_country
        existing.start_date = trip.start_date
        existing.nights = trip.nights
        existing.adults = trip.adults
        existing.children = trip.children
        existing.child_ages = trip.child_ages
        existing.budget = trip.budget
        existing.status = trip.status

        # Replace cities
        existing.cities.clear()
        for c in trip.cities:
            existing.cities.append(
                TripCity(
                    trip_city_id=c.trip_city_id,
                    trip_id=existing.trip_id,
                    city_name=c.city_name,
                    nights=c.nights,
                    sequence_order=c.sequence_order,
                )
            )

        # Replace items
        existing.items.clear()
        for it in trip.items:
            existing.items.append(
                TripItem(
                    item_id=it.item_id,
                    trip_id=existing.trip_id,
                    item_type=it.item_type,
                    catalogue_id=it.catalogue_id,
                    city_name=it.city_name,
                    start_datetime=it.start_datetime,
                    end_datetime=it.end_datetime,
                    price=it.price,
                    quantity=it.quantity,
                    item_details=it.item_details,
                )
            )

        self.session.flush()
        return existing

    def save_trip_from_dict(self, data: dict[str, Any]) -> Trip:
        """
        Create or update a Trip directly from a dictionary payload.
        Handles ISO date strings and item conversions.
        """
        start_date_val = data["start_date"]
        if isinstance(start_date_val, str):
            start_date_val = date.fromisoformat(start_date_val)

        trip = Trip(
            trip_id=data.get("trip_id"),
            departure_city=data["departure_city"],
            destination_country=data["destination_country"],
            start_date=start_date_val,
            nights=int(data["nights"]),
            adults=int(data["adults"]),
            children=int(data.get("children", 0)),
            child_ages=data.get("child_ages", []),
            budget=Decimal(str(data["budget"])),
            status=data.get("status", "DRAFT"),
        )

        for c in data.get("cities", []):
            trip.cities.append(
                TripCity(
                    trip_city_id=c.get("trip_city_id"),
                    city_name=c["city_name"],
                    nights=int(c["nights"]),
                    sequence_order=int(c["sequence_order"]),
                )
            )

        for item_data in data.get("items", []):
            start_dt = item_data["start_datetime"]
            if isinstance(start_dt, str):
                start_dt = datetime.fromisoformat(start_dt)

            end_dt = item_data.get("end_datetime")
            if isinstance(end_dt, str):
                end_dt = datetime.fromisoformat(end_dt)

            trip.items.append(
                TripItem(
                    item_id=item_data.get("item_id"),
                    item_type=item_data["item_type"],
                    catalogue_id=item_data["catalogue_id"],
                    city_name=item_data.get("city_name"),
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    price=Decimal(str(item_data["price"])),
                    quantity=int(item_data.get("quantity", 1)),
                    item_details=item_data.get("item_details", {}),
                )
            )

        return self.save_trip(trip)

    def delete_trip(self, trip_id: str) -> bool:
        """Delete a trip by trip_id. Cascade deletes related cities and items."""
        trip = self.get_trip_by_id(trip_id)
        if trip:
            self.session.delete(trip)
            self.session.flush()
            return True
        return False

    def list_trips(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> list[Trip]:
        """List trips with pagination and optional status filter."""
        stmt = select(Trip).order_by(Trip.created_at.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Trip.status == status)
        return list(self.session.scalars(stmt).all())

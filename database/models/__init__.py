"""
SQLAlchemy 2.0 ORM models for Build My Holiday application-owned persistence.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarative class for all application persistence models."""
    pass


from database.models.trip import Trip
from database.models.trip_city import TripCity
from database.models.trip_item import TripItem
from database.models.reservation import Reservation, ReservationItem

__all__ = [
    "Base",
    "Trip",
    "TripCity",
    "TripItem",
    "Reservation",
    "ReservationItem",
]

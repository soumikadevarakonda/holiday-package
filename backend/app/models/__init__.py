"""SQLAlchemy 2.0 ORM models for the app-state tables (Person B).

The tables are created by database/schema/006–011_*.sql (MySQL) or Base.metadata.create_all (tests, SQLite).
Keep the two in sync: a column added here needs a new numbered SQL file too.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarative class for all application persistence models."""


from app.models.trip import Trip  # noqa: E402
from app.models.package import Package, PackageVersion  # noqa: E402
from app.models.reservation import Reservation, ReservationItem  # noqa: E402
from app.models.inventory import InventoryUsage  # noqa: E402

__all__ = ["Base", "Trip", "Package", "PackageVersion", "Reservation", "ReservationItem", "InventoryUsage"]

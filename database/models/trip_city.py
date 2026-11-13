"""
TripCity ORM model.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models import Base

if TYPE_CHECKING:
    from database.models.trip import Trip


class TripCity(Base):
    """
    An individual city destination within a multi-city holiday trip.
    """

    __tablename__ = "trip_cities"

    trip_city_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"tc-{uuid.uuid4().hex[:12]}",
    )
    trip_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("trips.trip_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    city_name: Mapped[str] = mapped_column(String(100), nullable=False)
    nights: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="cities")

    __table_args__ = (
        UniqueConstraint("trip_id", "sequence_order", name="uq_trip_city_sequence"),
        CheckConstraint("nights >= 1", name="chk_trip_cities_nights"),
        CheckConstraint("sequence_order >= 1", name="chk_trip_cities_seq"),
        Index("idx_trip_cities_trip_id", "trip_id"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert TripCity to dictionary."""
        return {
            "trip_city_id": self.trip_city_id,
            "trip_id": self.trip_id,
            "city_name": self.city_name,
            "nights": self.nights,
            "sequence_order": self.sequence_order,
        }

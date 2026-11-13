"""
Package and PackageVersion ORM models for versioned package persistence.
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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models import Base

if TYPE_CHECKING:
    from app.models.trip import Trip


class Package(Base):
    """
    Persisted holiday package entity.
    Maintains a pointer to the current active version number and tracks version history.
    """

    __tablename__ = "packages"

    package_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"pkg-{uuid.uuid4().hex[:12]}",
    )
    trip_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("trips.trip_id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PLANNED",
    )
    current_version_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    city_plans: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    trip: Mapped[Optional["Trip"]] = relationship("Trip")
    versions: Mapped[list["PackageVersion"]] = relationship(
        "PackageVersion",
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="PackageVersion.version_no",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'PLANNED', 'BOOKED', 'CANCELLED', 'OVER_BUDGET')",
            name="chk_packages_status",
        ),
        CheckConstraint("current_version_no >= 1", name="chk_packages_version_no"),
        CheckConstraint("total_price >= 0.00", name="chk_packages_total_price"),
        Index("idx_packages_trip_id", "trip_id"),
        Index("idx_packages_status", "status"),
    )

    @property
    def current_version(self) -> Optional["PackageVersion"]:
        """Return the current active PackageVersion object."""
        for v in self.versions:
            if v.version_no == self.current_version_no:
                return v
        return self.versions[-1] if self.versions else None

    def to_dict(self) -> dict[str, Any]:
        """Convert Package to API response dictionary."""
        current_v = self.current_version
        snapshot = current_v.snapshot if current_v else {}
        return {
            "package_id": self.package_id,
            "trip_id": self.trip_id,
            "status": self.status,
            "version_no": self.current_version_no,
            "total_price": float(self.total_price),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "package_data": snapshot,
            "city_plans": self.city_plans or [],
        }


class PackageVersion(Base):
    """
    Immutable snapshot of a package version.
    Every accepted change or rebuild appends a new version without overwriting history.
    """

    __tablename__ = "package_versions"

    version_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        default=lambda: f"ver-{uuid.uuid4().hex[:12]}",
    )
    package_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("packages.package_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    version_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    change_summary: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    package: Mapped["Package"] = relationship("Package", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("package_id", "version_no", name="uq_package_version_no"),
        CheckConstraint("version_no >= 1", name="chk_package_version_num"),
        Index("idx_package_versions_pkg_id", "package_id"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert PackageVersion to dictionary."""
        return {
            "version_id": self.version_id,
            "package_id": self.package_id,
            "version_no": self.version_no,
            "snapshot": self.snapshot,
            "change_summary": self.change_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

"""
Package and PackageVersion repository for data access and version management.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from database.models.package import Package, PackageVersion
from database.models.trip import Trip


class PackageRepository:
    """Repository managing trips, packages, and their immutable version history."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # --------------------------------------------------------------------------
    # Trip Requests
    # --------------------------------------------------------------------------

    def save_trip_request(self, data: dict[str, Any]) -> Trip:
        """Create or update a Trip request record."""
        start_date_val = data["start_date"]
        if isinstance(start_date_val, str):
            start_date_val = date.fromisoformat(start_date_val)

        trip_id = data.get("trip_id")
        existing: Optional[Trip] = None
        if trip_id:
            existing = self.session.get(Trip, trip_id)

        if existing is None:
            trip = Trip(
                trip_id=trip_id,
                departure_city=data["departure_city"],
                destination_country=data["destination_country"],
                start_date=start_date_val,
                nights=int(data["nights"]),
                adults=int(data["adults"]),
                children=int(data.get("children", 0)),
                child_ages=data.get("child_ages", []),
                budget=Decimal(str(data["budget"])),
                status=data.get("status", "PLANNED"),
            )
            self.session.add(trip)
            self.session.flush()
            return trip

        existing.departure_city = data["departure_city"]
        existing.destination_country = data["destination_country"]
        existing.start_date = start_date_val
        existing.nights = int(data["nights"])
        existing.adults = int(data["adults"])
        existing.children = int(data.get("children", 0))
        existing.child_ages = data.get("child_ages", [])
        existing.budget = Decimal(str(data["budget"]))
        existing.status = data.get("status", existing.status)
        self.session.flush()
        return existing

    def get_trip_request(self, trip_id: str) -> Optional[Trip]:
        """Fetch trip request by trip_id."""
        return self.session.get(Trip, trip_id)

    # --------------------------------------------------------------------------
    # Packages & Versions
    # --------------------------------------------------------------------------

    def create_package(
        self,
        package_id: str,
        initial_data: dict[str, Any],
        trip_id: Optional[str] = None,
        status: str = "PLANNED",
        total_price: Decimal = Decimal("0.00"),
        city_plans: Optional[list[dict[str, Any]]] = None,
    ) -> Package:
        """Create a new Package and its initial Version 1 snapshot."""
        package = Package(
            package_id=package_id,
            trip_id=trip_id,
            status=status,
            current_version_no=1,
            total_price=total_price,
            city_plans=city_plans or [],
        )
        self.session.add(package)
        self.session.flush()

        initial_version = PackageVersion(
            package_id=package_id,
            version_no=1,
            snapshot=initial_data,
            change_summary="Initial package build",
        )
        self.session.add(initial_version)
        self.session.flush()
        return package

    def get_package(self, package_id: str) -> Optional[Package]:
        """Retrieve package by primary key package_id."""
        return self.session.get(Package, package_id)

    def save_version(
        self,
        package_id: str,
        snapshot: dict[str, Any],
        change_summary: Optional[str] = None,
        new_total_price: Optional[Decimal] = None,
    ) -> PackageVersion:
        """
        Append a new immutable version to the package without overwriting previous versions.
        Increments current_version_no and updates package total price.
        """
        package = self.get_package(package_id)
        if package is None:
            raise ValueError(f"Package '{package_id}' not found")

        next_version_no = package.current_version_no + 1
        new_version = PackageVersion(
            package_id=package_id,
            version_no=next_version_no,
            snapshot=snapshot,
            change_summary=change_summary or f"Applied change to version {next_version_no}",
        )
        self.session.add(new_version)

        package.current_version_no = next_version_no
        if new_total_price is not None:
            package.total_price = new_total_price
        self.session.flush()
        return new_version

    def get_version(self, package_id: str, version_no: int) -> Optional[PackageVersion]:
        """Retrieve a specific historical version snapshot."""
        stmt = select(PackageVersion).where(
            PackageVersion.package_id == package_id,
            PackageVersion.version_no == version_no,
        )
        return self.session.scalars(stmt).first()

    def get_version_history(self, package_id: str) -> list[PackageVersion]:
        """List all version snapshots for a package in chronological order."""
        stmt = (
            select(PackageVersion)
            .where(PackageVersion.package_id == package_id)
            .order_by(PackageVersion.version_no.asc())
        )
        return list(self.session.scalars(stmt).all())

    def restore_version(self, package_id: str, target_version_no: int) -> Package:
        """
        Undo operation: restores a previous historical snapshot by appending it
        as a brand new version number. Never deletes or mutates history!
        """
        target_version = self.get_version(package_id, target_version_no)
        if target_version is None:
            raise ValueError(f"Historical version {target_version_no} not found for package '{package_id}'")

        # Snapshot from target version
        restored_snapshot = dict(target_version.snapshot)
        new_price = None
        if "total_price" in restored_snapshot:
            new_price = Decimal(str(restored_snapshot["total_price"]))
        elif "total_inr" in restored_snapshot:
            new_price = Decimal(str(restored_snapshot["total_inr"]))

        self.save_version(
            package_id=package_id,
            snapshot=restored_snapshot,
            change_summary=f"Restored version {target_version_no}",
            new_total_price=new_price,
        )
        return self.get_package(package_id)

    def update_package_status(self, package_id: str, status: str) -> Optional[Package]:
        """Update package status (e.g. 'BOOKED', 'CANCELLED')."""
        package = self.get_package(package_id)
        if package:
            package.status = status
            self.session.flush()
        return package

    def list_packages(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> list[Package]:
        """List packages with pagination and optional status filter."""
        stmt = select(Package).order_by(desc(Package.created_at)).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Package.status == status)
        return list(self.session.scalars(stmt).all())

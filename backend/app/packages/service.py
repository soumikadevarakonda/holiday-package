"""
Package service orchestrating request validation, engine build, persistence, and versioning.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.engine_adapter import get_engine_adapter
from backend.app.core.errors import BadRequestError, ConflictError, NotFoundError
from backend.app.packages.repository import PackageRepository
from backend.app.packages.schemas import TripRequestSchema
from backend.app.packages.timeline import generate_package_timeline


class PackageService:
    """Service managing package generation, retrieval, city-plan selection, and undo."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = PackageRepository(session)
        self.engine_adapter = get_engine_adapter()

    def create_package(self, request_data: TripRequestSchema) -> dict[str, Any]:
        """
        Create a new package:
        1. Persist validated trip request.
        2. Invoke engine adapter's build().
        3. Persist package and version snapshot on success.
        4. Handle OVER_BUDGET and NO_PACKAGE outcomes.
        """
        # Step 1: Persist the trip request
        trip_dict = request_data.model_dump()
        trip_id = f"trip-{uuid.uuid4().hex[:12]}"
        trip_dict["trip_id"] = trip_id
        persisted_trip = self.repo.save_trip_request(trip_dict)

        # Step 2: Invoke package builder via engine adapter
        # (Raises EngineUnavailableError / HTTP 503 if Person A's engine is not yet available)
        build_result = self.engine_adapter.build(request_data)

        # Extract outcome
        outcome = getattr(build_result, "outcome", "PACKAGE")
        package_obj = getattr(build_result, "package", build_result)
        city_plans = getattr(build_result, "city_plans", [])

        # If package_obj is a dataclass or model, convert to dict
        if hasattr(package_obj, "to_dict"):
            pkg_data = package_obj.to_dict()
        elif isinstance(package_obj, dict):
            pkg_data = package_obj
        else:
            pkg_data = {"raw": str(package_obj)}

        pkg_id = pkg_data.get("trip_id") or f"pkg-{uuid.uuid4().hex[:12]}"
        pkg_data["trip_id"] = pkg_id

        # Total price
        total_price = Decimal(str(pkg_data.get("total_inr") or pkg_data.get("total_price") or 0))

        if outcome == "PACKAGE":
            package = self.repo.create_package(
                package_id=pkg_id,
                trip_id=persisted_trip.trip_id,
                initial_data=pkg_data,
                status="PLANNED",
                total_price=total_price,
                city_plans=city_plans,
            )
            timeline = generate_package_timeline(
                pkg_data,
                request_data.start_date,
                request_data.nights,
            )
            return {
                "outcome": "PACKAGE",
                "package_id": package.package_id,
                "trip_id": persisted_trip.trip_id,
                "status": package.status,
                "version": package.current_version_no,
                "version_no": package.current_version_no,
                "total_price": float(package.total_price),
                "total_inr": int(package.total_price),
                "items": pkg_data.get("items", []),
                "package_data": pkg_data,
                "package": pkg_data,
                "timeline": timeline,
                "city_plans": city_plans or [],
            }

        elif outcome == "OVER_BUDGET":
            package = self.repo.create_package(
                package_id=pkg_id,
                trip_id=persisted_trip.trip_id,
                initial_data=pkg_data,
                status="OVER_BUDGET",
                total_price=total_price,
                city_plans=city_plans,
            )
            return {
                "outcome": "OVER_BUDGET",
                "package_id": package.package_id,
                "cheapest_total": getattr(build_result, "cheapest_total", float(total_price)),
                "over_by": getattr(build_result, "over_by", float(total_price - request_data.budget)),
                "suggestion": getattr(build_result, "suggestion", "Raise budget or decrease duration by 1 night"),
                "cheapest_package": pkg_data,
            }

        else:  # NO_PACKAGE
            return {
                "outcome": "NO_PACKAGE",
                "reason": getattr(build_result, "reason", "No feasible package fits the requested constraints"),
                "trip_id": persisted_trip.trip_id,
            }

    def get_package(self, package_id: str) -> dict[str, Any]:
        """Retrieve persisted package details and day-by-day plan."""
        package = self.repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")

        current_v = package.current_version
        snapshot = current_v.snapshot if current_v else {}

        # Generate timeline
        start_d = snapshot.get("start_date")
        nights = 0
        if "items" in snapshot:
            # Estimate nights from hotel items or dates if trip not linked
            if snapshot.get("start_date") and snapshot.get("end_date"):
                from datetime import date
                d1 = date.fromisoformat(str(snapshot["start_date"])[:10])
                d2 = date.fromisoformat(str(snapshot["end_date"])[:10])
                nights = (d2 - d1).days

        if package.trip:
            start_d = package.trip.start_date
            nights = package.trip.nights

        timeline = []
        if start_d and nights > 0:
            timeline = generate_package_timeline(snapshot, start_d, nights)

        return {
            "package_id": package.package_id,
            "trip_id": package.trip_id,
            "status": package.status,
            "version": package.current_version_no,
            "version_no": package.current_version_no,
            "total_price": float(package.total_price),
            "total_inr": int(package.total_price),
            "created_at": package.created_at.isoformat() if package.created_at else None,
            "updated_at": package.updated_at.isoformat() if package.updated_at else None,
            "items": snapshot.get("items", []),
            "package_data": snapshot,
            "package": snapshot,
            "timeline": timeline,
            "city_plans": package.city_plans or [],
        }

    def get_city_plans(self, package_id: str) -> list[dict[str, Any]]:
        """Retrieve alternative city plans for a package."""
        package = self.repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")
        return package.city_plans or []

    def rebuild_package(self, package_id: str, city_plan: dict[str, Any]) -> dict[str, Any]:
        """
        Rebuild package on a chosen city plan:
        1. Retrieve existing package and trip request.
        2. Call engine rebuild().
        3. Save new version and return updated package.
        """
        package = self.repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")

        current_v = package.current_version
        snapshot = current_v.snapshot if current_v else {}

        # Call engine rebuild
        rebuild_result = self.engine_adapter.rebuild(snapshot, city_plan)
        new_pkg_obj = getattr(rebuild_result, "package", rebuild_result)
        new_data = new_pkg_obj.to_dict() if hasattr(new_pkg_obj, "to_dict") else dict(new_pkg_obj)

        new_price = Decimal(str(new_data.get("total_inr") or new_data.get("total_price") or 0))

        # Append as new version
        new_version = self.repo.save_version(
            package_id=package_id,
            snapshot=new_data,
            change_summary=f"Rebuilt with city plan: {city_plan.get('label', 'custom')}",
            new_total_price=new_price,
        )

        return self.get_package(package_id)

    def undo_package(self, package_id: str) -> dict[str, Any]:
        """
        Restore previous historical version under a new version number.
        """
        package = self.repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")

        if package.current_version_no <= 1:
            raise ConflictError("Cannot undo: package is at its initial version 1", code="CANNOT_UNDO")

        target_version_no = package.current_version_no - 1
        self.repo.restore_version(package_id, target_version_no)
        pkg_details = self.get_package(package_id)

        return {
            "message": f"Successfully restored to version {target_version_no}",
            "version": pkg_details["version"],
            "version_no": pkg_details["version_no"],
            "package": pkg_details,
        }

    def list_packages(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
    ) -> dict[str, Any]:
        """List persisted packages."""
        packages = self.repo.list_packages(limit=limit, offset=offset, status=status)
        return {
            "count": len(packages),
            "packages": [self.get_package(pkg.package_id) for pkg in packages],
        }

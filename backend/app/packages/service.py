"""
Package service orchestrating request validation, engine build, persistence, and versioning.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.engine_adapter import get_engine_adapter
from app.core.errors import ConflictError, NotFoundError
from app.packages.repository import PackageRepository
from app.packages.schemas import TripRequestSchema
from app.packages.timeline import generate_package_timeline

ITEM_TYPES = ("flight", "hotel", "transfer", "attraction")


def compute_totals(pkg_data: dict[str, Any]) -> dict[str, Any]:
    """M5: total, budget, left / over, and the total per part type."""
    by_type = {t: 0 for t in ITEM_TYPES}
    for it in pkg_data.get("items", []):
        by_type[it.get("type", "other")] = by_type.get(it.get("type", "other"), 0) + int(it.get("price_inr", 0))
    total = sum(by_type.values())
    budget = int(pkg_data.get("budget_inr") or 0)
    return {"total_inr": total, "budget_inr": budget, "left_inr": budget - total,
            "over_budget": total > budget, "by_type": by_type}


def _new_package_id() -> str:
    return f"pkg-{uuid.uuid4().hex[:12]}"


class PackageService:
    """Service managing package generation, retrieval, city-plan selection, and undo."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = PackageRepository(session)
        self.engine_adapter = get_engine_adapter()

    def _package_view(self, pkg_id: str, pkg_data: dict[str, Any], status: str, version: int) -> dict[str, Any]:
        start, end = date.fromisoformat(pkg_data["start_date"]), date.fromisoformat(pkg_data["end_date"])
        return {
            "package_id": pkg_id,
            "status": status,
            "version": version,
            "version_no": version,
            "total_inr": int(pkg_data.get("total_inr", 0)),
            "totals": compute_totals(pkg_data),
            "items": pkg_data.get("items", []),
            "package": pkg_data,
            "timeline": generate_package_timeline(pkg_data, start, (end - start).days),
        }

    def create_package(self, request_data: TripRequestSchema) -> dict[str, Any]:
        """
        Create a new package:
        1. Persist the validated trip request.
        2. Build through the engine adapter.
        3. PACKAGE / OVER_BUDGET: persist the package as version 1 (the cheapest one for OVER_BUDGET, so it
           can be viewed); NO_PACKAGE: return the reason.
        """
        trip_dict = request_data.model_dump()
        trip_dict["trip_id"] = f"trip-{uuid.uuid4().hex[:12]}"
        persisted_trip = self.repo.save_trip_request(trip_dict)

        build_result = self.engine_adapter.build(request_data)
        outcome = build_result.outcome
        city_plans = build_result.city_plans or []

        if outcome == "NO_PACKAGE":
            return {"outcome": "NO_PACKAGE", "reason": build_result.reason, "trip_id": persisted_trip.trip_id,
                    "city_plans": city_plans}

        pkg_data = dict(build_result.package)
        pkg_id = _new_package_id()
        pkg_data["trip_id"] = pkg_id
        status = "PLANNED" if outcome == "PACKAGE" else "OVER_BUDGET"
        package = self.repo.create_package(
            package_id=pkg_id,
            trip_id=persisted_trip.trip_id,
            initial_data=pkg_data,
            status=status,
            total_price=Decimal(str(pkg_data.get("total_inr", 0))),
            city_plans=city_plans,
        )
        view = self._package_view(package.package_id, pkg_data, package.status, package.current_version_no)
        view.update({"outcome": outcome, "trip_id": persisted_trip.trip_id, "city_plans": city_plans,
                     "alternatives": build_result.alternatives or {}})
        if outcome == "OVER_BUDGET":
            view.update({"cheapest_total": build_result.cheapest_total, "over_by": build_result.over_by,
                         "suggestion": build_result.suggestion, "cheapest_package": pkg_data})
        return view

    def get_package(self, package_id: str) -> dict[str, Any]:
        """Persisted package, its current version, totals and the day-by-day plan (survives restart)."""
        package = self.repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")
        current_v = package.current_version
        snapshot = current_v.snapshot if current_v else {}
        view = self._package_view(package.package_id, snapshot, package.status, package.current_version_no)
        view.update({
            "trip_id": package.trip_id,
            "city_plans": package.city_plans or [],
            "created_at": package.created_at.isoformat() if package.created_at else None,
            "updated_at": package.updated_at.isoformat() if package.updated_at else None,
        })
        return view

    def get_city_plans(self, package_id: str) -> list[dict[str, Any]]:
        """G3: ranked city plans with totals."""
        package = self.repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")
        return package.city_plans or []

    def rebuild_package(self, package_id: str, city_plan: Any, base_version: int | None = None) -> dict[str, Any]:
        """G3: rebuild on another city plan and save it as a new version."""
        package = self.repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")
        if package.status == "BOOKED":
            raise ConflictError("Cannot rebuild a confirmed package", code="ALREADY_BOOKED")
        if base_version is not None and base_version != package.current_version_no:
            raise ConflictError(f"Version conflict: current version is {package.current_version_no}",
                                code="VERSION_CONFLICT", details={"current_version": package.current_version_no})

        snapshot = package.current_version.snapshot
        result = self.engine_adapter.rebuild(snapshot, city_plan)
        new_data = dict(result.package)
        new_data["trip_id"] = package_id
        label = " → ".join(f"{c['city']} ({c['nights']}N)" for c in new_data.get("city_plan", []))
        self.repo.save_version(package_id=package_id, snapshot=new_data, change_summary=f"Rebuilt on {label}",
                               new_total_price=Decimal(str(new_data.get("total_inr", 0))))
        if package.status == "OVER_BUDGET":
            package.status = "PLANNED"
        return self.get_package(package_id)

    def undo_package(self, package_id: str) -> dict[str, Any]:
        """Restore the previous version as a new version (history is never rewritten)."""
        package = self.repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")
        if package.status == "BOOKED":
            raise ConflictError("Cannot undo a confirmed package", code="ALREADY_BOOKED")
        if package.current_version_no <= 1:
            raise ConflictError("Cannot undo: package is at its initial version 1", code="CANNOT_UNDO")

        target_version_no = package.current_version_no - 1
        self.repo.restore_version(package_id, target_version_no)
        pkg_details = self.get_package(package_id)
        return {
            "message": f"Restored version {target_version_no}",
            "version": pkg_details["version"],
            "version_no": pkg_details["version_no"],
            "package": pkg_details,
        }

    def list_packages(self, limit: int = 20, offset: int = 0, status: str | None = None) -> dict[str, Any]:
        packages = self.repo.list_packages(limit=limit, offset=offset, status=status)
        return {"count": len(packages), "packages": [self.get_package(pkg.package_id) for pkg in packages]}

"""
Service layer for component alternatives (Feature G2) and change application (Feature M6).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.engine_adapter import get_engine_adapter
from backend.app.core.errors import ConflictError, NotFoundError
from backend.app.packages.repository import PackageRepository
from backend.app.packages.schemas import ComponentChangeRequest


class ChangesService:
    """Service providing alternative components and applying swaps with versioning."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.package_repo = PackageRepository(session)
        self.engine_adapter = get_engine_adapter()

    def get_options(
        self,
        package_id: str,
        kind: str,
        **params: Any,
    ) -> list[dict[str, Any]]:
        """
        Retrieve valid alternative options for a component type with price differences.
        Calls engine adapter's options(pkg, kind, **params).
        """
        package = self.package_repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")

        current_v = package.current_version
        snapshot = current_v.snapshot if current_v else {}

        # Call engine adapter
        options_result = self.engine_adapter.options(snapshot, kind, **params)

        # Standardize return list
        if isinstance(options_result, list):
            return [
                opt.to_dict() if hasattr(opt, "to_dict") else dict(opt)
                for opt in options_result
            ]
        return []

    def apply_change(
        self,
        package_id: str,
        change_req: ComponentChangeRequest,
    ) -> dict[str, Any]:
        """
        Apply a component change to a package:
        1. Retrieve current active package snapshot.
        2. Pass change to engine adapter's apply_change().
        3. Validate resulting package through engine adapter's validate().
        4. If violations occur, return 409 Conflict with RULE_VIOLATION.
        5. If valid, increment version number and persist new snapshot.
        """
        package = self.package_repo.get_package(package_id)
        if package is None:
            raise NotFoundError(f"Package '{package_id}' not found")

        if package.status == "BOOKED":
            raise ConflictError("Cannot modify a confirmed and booked package")

        if change_req.base_version is not None and change_req.base_version != package.current_version_no:
            raise ConflictError(
                message=f"Version conflict: current package version is {package.current_version_no}, but base_version was {change_req.base_version}",
                code="VERSION_CONFLICT",
            )

        current_v = package.current_version
        snapshot = current_v.snapshot if current_v else {}

        # 1. Apply change via engine
        change_payload = change_req.model_dump()
        change_result = self.engine_adapter.apply_change(snapshot, change_payload)

        # Extract new package from change_result
        new_pkg_obj = getattr(change_result, "package", change_result)
        new_snapshot = new_pkg_obj.to_dict() if hasattr(new_pkg_obj, "to_dict") else dict(new_pkg_obj)

        # 2. Validate resulting package
        violations = self.engine_adapter.validate(new_snapshot)
        if violations:
            raise ConflictError(
                message="Change violates travel constraints",
                code="RULE_VIOLATION",
                details={"violations": violations},
            )

        # 3. Save new version
        new_price = Decimal(str(new_snapshot.get("total_inr") or new_snapshot.get("total_price") or 0))
        summary = f"Changed {change_req.kind} to {change_req.new_catalog_id}"

        new_version = self.package_repo.save_version(
            package_id=package_id,
            snapshot=new_snapshot,
            change_summary=summary,
            new_total_price=new_price,
        )

        return {
            "message": "Component change applied successfully",
            "package_id": package_id,
            "version": new_version.version_no,
            "version_no": new_version.version_no,
            "total_price": float(package.total_price),
            "items": new_snapshot.get("items", []),
            "package": new_snapshot,
            "side_effects": getattr(change_result, "side_effects", []),
            "warnings": getattr(change_result, "warnings", []),
        }

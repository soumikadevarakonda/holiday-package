"""Violation type (defined in the shared model) and helpers for the checks."""

from app.core.package_model import Violation

__all__ = ["Violation", "to_dicts"]


def to_dicts(violations: list[Violation]) -> list[dict]:
    return [{"rule_id": v.rule_id, "item_ref": v.item_ref, "message": v.message} for v in violations]

"""Package totals and budget tracking (M5)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.package_model import Totals

if TYPE_CHECKING:
    from app.core.package_model import Item


def compute_totals(items: list[Item], budget_inr: int) -> Totals:
    """Sum line items by component type and compute total and budget difference."""
    by_type: dict[str, int] = {
        "flight": 0,
        "hotel": 0,
        "transfer": 0,
        "attraction": 0,
    }

    for item in items:
        if item.type in by_type:
            by_type[item.type] += item.price_inr
        else:
            by_type[item.type] = item.price_inr

    total_inr = sum(by_type.values())
    return Totals(total_inr=total_inr, budget_inr=budget_inr, by_type=by_type)

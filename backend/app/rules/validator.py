"""The validator: every travel rule (brief section 4) as a check with an ID.  (Person A)

Used by build, every change, confirm and export. A package is valid only if this returns [].
"""

from __future__ import annotations

from app.catalog.store import CatalogStore
from app.core.package_model import Package, Violation
from app.rules.checks import airport_transfers, attractions, dates, flights, hotels, intercity, prices
from app.rules.context import build_context


def validate(
    pkg: Package,
    *,
    initial: bool = False,
    seats_used: dict[str, int] | None = None,
    rooms_used: dict[tuple[str, str], int] | None = None,
    store: CatalogStore | None = None,
) -> list[Violation]:
    """Empty list = the package is valid.

    initial:    True for the package the builder first returns (enables A3: 1–2 attractions per full day).
    seats_used: S2, seats already booked per flight_id.
    rooms_used: S2, rooms already booked per (room_id, 'YYYY-MM-DD').
    """
    ctx = build_context(pkg, store)
    out = list(ctx.errors)
    out += dates.check(ctx)
    out += flights.check(ctx, seats_used)
    out += airport_transfers.check(ctx)
    out += intercity.check(ctx)
    out += hotels.check(ctx, rooms_used)
    out += attractions.check(ctx, initial=initial)
    out += prices.check(ctx)
    return out

"""Valid alternatives for a package part, each with price_diff (M6, G2).  (Person A)

PHASE 0 STUB: returns the package's current choice as the only option (price_diff 0).
"""

from app.core.package_model import Option, OptionKind, Package

_ITEM_TYPE = {"hotel": "hotel", "flight": "flight", "attraction": "attraction"}


def options(pkg: Package, kind: OptionKind, **params) -> list[Option]:
    """kind="hotel" (params: city), "flight" (params: leg="arrival"|"return"), "attraction" (params: date)."""
    items = [i for i in pkg.items if i.type == _ITEM_TYPE[kind]]
    if kind == "hotel" and params.get("city"):
        items = [i for i in items if i.city == params["city"]]
    if kind == "flight" and params.get("leg"):
        items = items[:1] if params["leg"] == "arrival" else items[-1:]
    if kind == "attraction" and params.get("date"):
        items = [i for i in items if i.start.startswith(params["date"])]
    return [Option(kind=kind, catalog_id=i.catalog_id, label=i.name, price_inr=i.price_inr, price_diff=0,
                   room_id=i.room_id, start=i.start if kind == "attraction" else None) for i in items]

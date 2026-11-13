"""P1: every line price follows its formula (within 1%), and quantities match."""

from __future__ import annotations

import math

from app.core.package_model import Violation
from app.pricing.calculator import (
    calculate_attraction_price,
    calculate_flight_price,
    calculate_hotel_price,
    calculate_transfer_price,
)
from app.rules.context import Ctx

TOLERANCE = 0.01


def _off(actual: int, expected: int) -> bool:
    return abs(actual - expected) > TOLERANCE * max(abs(expected), 1)


def check(ctx: Ctx) -> list[Violation]:
    v: list[Violation] = []
    A, C, T = ctx.adults, ctx.children, ctx.travelers

    def compare(item, expected: int, expected_qty: int) -> None:
        if item.quantity != expected_qty:
            v.append(Violation("P1", item.item_id, f"{item.name}: quantity {item.quantity}, expected {expected_qty}."))
        if _off(item.price_inr, expected):
            v.append(Violation("P1", item.item_id, f"{item.name}: price ₹{item.price_inr}, expected ₹{expected}."))

    for leg in ctx.flights:
        compare(leg.item, calculate_flight_price(leg.flight.price_per_seat, T), T)
    for s in ctx.stays:
        k = s.item.quantity
        if _off(s.item.price_inr, calculate_hotel_price(s.room.price_per_night, k, len(s.nights))):
            v.append(Violation("P1", s.item.item_id, f"{s.item.name}: price ₹{s.item.price_inr}, expected "
                               f"₹{calculate_hotel_price(s.room.price_per_night, k, len(s.nights))}."))
    for use in ctx.airport_transfers + ctx.intercity_transfers + ctx.city_transfers:
        t = use.transfer
        qty = math.ceil(T / t.max_passengers) if t.pricing == "PER_VEHICLE" else T
        compare(use.item, calculate_transfer_price(t.pricing, t.price, t.child_price, t.max_passengers, A, C), qty)
    for vis in ctx.visits:
        a = vis.attraction
        compare(vis.item, calculate_attraction_price(a.price_per_person, a.child_price, A, C), T)
    # total = sum of parts holds by construction (Package.total_inr is computed from the items)
    return v

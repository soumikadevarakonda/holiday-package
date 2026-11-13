"""Price formulas for all package components (M5, P1).

Formulas (all integer INR):
- Flight: price_per_seat * travelers
- Hotel: price_per_night * rooms * nights
- Transfer PER_PERSON: adults * price + children * (child_price if child_price is not None else price)
- Transfer PER_VEHICLE: price * ceil(travelers / max_passengers)
- Attraction: adults * price_per_person + children * (child_price if child_price is not None else price_per_person)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.catalog.models import Attraction, Flight, RoomType, Transfer


def calculate_flight_price(price_per_seat: int, travelers: int) -> int:
    """Every seat costs price_per_seat. Adults and children pay the same."""
    return price_per_seat * travelers


def calculate_hotel_price(price_per_night: int, rooms: int, nights: int) -> int:
    """Price of one room for one night * rooms * nights."""
    return price_per_night * rooms * nights


def calculate_transfer_price(
    pricing: str,
    price: int,
    child_price: int | None,
    max_passengers: int,
    adults: int,
    children: int,
) -> int:
    """Calculate transfer price for adults and children based on pricing model."""
    travelers = adults + children
    if pricing == "PER_VEHICLE":
        vehicles = math.ceil(travelers / max_passengers)
        return price * vehicles

    # PER_PERSON
    effective_child_price = child_price if child_price is not None else price
    return adults * price + children * effective_child_price


def calculate_attraction_price(
    price_per_person: int,
    child_price: int | None,
    adults: int,
    children: int,
) -> int:
    """Calculate entry price for an attraction.

    TRAP: child_price can be 0 (free for kids). Always check `is not None`.
    """
    effective_child_price = child_price if child_price is not None else price_per_person
    return adults * price_per_person + children * effective_child_price

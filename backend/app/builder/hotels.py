"""Hotels per city stay: every valid (hotel, room type, k), cheapest first. Greedy is optimal per city."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache

from app.catalog.models import Hotel, RoomType
from app.catalog.store import get_store
from app.pricing.calculator import calculate_hotel_price
from app.rules.checks.hotels import rooms_fit


@dataclass(frozen=True)
class StayOption:
    hotel: Hotel
    room: RoomType
    rooms: int          # k
    price: int


def smallest_k(adults: int, children: int, room: RoomType) -> int | None:
    for k in range(1, adults + 1):
        if rooms_fit(adults, children, k, room.max_adults, room.max_children):
            return k
    return None


@lru_cache(maxsize=4096)
def stay_options(city: str, check_in: date, nights: int, adults: int, children: int) -> tuple[StayOption, ...]:
    """All valid options for one city stay, sorted by price, then stars (desc), then hotel_id."""
    store = get_store()
    out = []
    dates = [(check_in + timedelta(days=i)).isoformat() for i in range(nights)]
    for hotel in store.get_hotels_in_city(city):
        for room in store.get_rooms_for_hotel(hotel.hotel_id):
            k = smallest_k(adults, children, room)
            if k is None:
                continue
            if all(store.get_rooms_left(room.room_id, d) >= k for d in dates):
                out.append(StayOption(hotel, room, k, calculate_hotel_price(room.price_per_night, k, nights)))
    out.sort(key=lambda o: (o.price, -o.hotel.stars, o.rooms, o.hotel.hotel_id, o.room.room_id))
    return tuple(out)


def clear_cache() -> None:
    stay_options.cache_clear()

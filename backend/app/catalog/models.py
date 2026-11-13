"""Dataclasses for all catalog entities (read-only source of truth)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

TransferPricing = Literal["PER_PERSON", "PER_VEHICLE"]


@dataclass(frozen=True)
class Airport:
    code: str
    name: str
    city: str
    country: str
    timezone: str
    lat: float | None = None
    lng: float | None = None
    serves_cities: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Flight:
    flight_id: str
    airline: str
    flight_number: str
    from_airport: str
    to_airport: str
    departure_local: str  # "YYYY-MM-DDTHH:MM:SS" or "YYYY-MM-DD HH:MM:SS"
    arrival_local: str
    stops: int
    duration_minutes: int
    price_per_seat: int
    seats_left: int
    cabin: str

    @property
    def departure_date(self) -> str:
        return self.departure_local[:10]

    @property
    def arrival_date(self) -> str:
        return self.arrival_local[:10]

    @property
    def departure_time(self) -> str:
        return self.departure_local[11:16]

    @property
    def arrival_time(self) -> str:
        return self.arrival_local[11:16]


@dataclass(frozen=True)
class Hotel:
    hotel_id: str
    name: str
    aliases: list[str]
    city: str
    area: str
    lat: float | None
    lng: float | None
    stars: int
    rating: float
    check_in_from: str
    check_out_until: str
    family_friendly: bool
    image: str | None


@dataclass(frozen=True)
class RoomType:
    room_id: str
    hotel_id: str
    room_type: str  # SINGLE, TWIN, DOUBLE, TRIPLE, FAMILY, FAMILY_SUITE
    name: str
    max_adults: int
    max_children: int
    price_per_night: int
    refundable: bool


@dataclass(frozen=True)
class RoomAvailability:
    room_id: str
    date: str  # "YYYY-MM-DD"
    rooms_left: int


@dataclass(frozen=True)
class Transfer:
    transfer_id: str
    type: str  # AIRPORT_TAXI, AIRPORT_BUS, TRAIN, etc.
    name: str
    from_point: str
    to_point: str
    max_passengers: int
    service_from: str
    service_until: str
    duration_minutes: int
    pricing: TransferPricing
    price: int
    child_price: int | None
    airport_code: str | None = None
    city: str | None = None
    area: str | None = None
    from_city: str | None = None
    to_city: str | None = None
    frequency_minutes: int | None = None
    door_to_door: bool | None = None


@dataclass(frozen=True)
class Attraction:
    attraction_id: str
    name: str
    name_ja: str | None
    city: str
    category: str
    lat: float | None
    lng: float | None
    open_days: list[str]  # ["MON", "TUE", ...]
    open_from: str
    open_until: str
    closed_dates: list[str]
    aliases: list[str]
    visit_minutes: int
    child_friendly: bool
    accessible: bool
    price_per_person: int
    child_price: int | None
    image: str | None


@dataclass(frozen=True)
class Country:
    code: str
    name: str
    timezone: str
    cities: list[str]


@dataclass(frozen=True)
class DepartureCity:
    city: str
    airport: str


@dataclass(frozen=True)
class IntercityLink:
    country_code: str
    from_city: str
    to_city: str
    transfer_ids: list[str]


@dataclass(frozen=True)
class RulesMeta:
    min_nights: int
    max_nights: int
    min_nights_per_city: int
    first_night: str
    last_departure: str

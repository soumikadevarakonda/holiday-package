"""Catalog lookup indexes for fast O(1) queries during building and validation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from app.catalog.models import (
    Airport,
    Attraction,
    Country,
    DepartureCity,
    Flight,
    Hotel,
    IntercityLink,
    RoomAvailability,
    RoomType,
    RulesMeta,
    Transfer,
)


@dataclass
class CatalogIndexes:
    # Airports
    airports_by_code: dict[str, Airport] = field(default_factory=dict)
    airports_serving_city: dict[str, list[Airport]] = field(default_factory=lambda: defaultdict(list))
    airports_by_city: dict[str, list[Airport]] = field(default_factory=lambda: defaultdict(list))

    # Flights
    flights_by_id: dict[str, Flight] = field(default_factory=dict)
    # Key: (from_airport, arr_date "YYYY-MM-DD")
    flights_by_from_and_arr_date: dict[tuple[str, str], list[Flight]] = field(default_factory=lambda: defaultdict(list))
    # Key: (to_airport, dep_date "YYYY-MM-DD")
    flights_by_to_and_dep_date: dict[tuple[str, str], list[Flight]] = field(default_factory=lambda: defaultdict(list))

    # Hotels & Rooms
    hotels_by_id: dict[str, Hotel] = field(default_factory=dict)
    hotels_by_city: dict[str, list[Hotel]] = field(default_factory=lambda: defaultdict(list))
    rooms_by_id: dict[str, RoomType] = field(default_factory=dict)
    rooms_by_hotel: dict[str, list[RoomType]] = field(default_factory=lambda: defaultdict(list))
    # Key: (room_id, date "YYYY-MM-DD") -> rooms_left
    availability: dict[tuple[str, str], int] = field(default_factory=dict)

    # Transfers
    transfers_by_id: dict[str, Transfer] = field(default_factory=dict)
    # Key: (airport_code, city) -> list[Transfer]
    airport_transfers_by_airport_city: dict[tuple[str, str], list[Transfer]] = field(default_factory=lambda: defaultdict(list))
    # Key: (from_city, to_city) -> list[Transfer]
    intercity_transfers_by_route: dict[tuple[str, str], list[Transfer]] = field(default_factory=lambda: defaultdict(list))
    # Key: (from_city, to_city) -> list of transfer_ids
    link_transfer_ids: dict[tuple[str, str], list[str]] = field(default_factory=lambda: defaultdict(list))

    # Attractions
    attractions_by_id: dict[str, Attraction] = field(default_factory=dict)
    attractions_by_city: dict[str, list[Attraction]] = field(default_factory=lambda: defaultdict(list))

    # Geography & Rules
    countries_by_name: dict[str, Country] = field(default_factory=dict)
    countries_by_code: dict[str, Country] = field(default_factory=dict)
    departure_cities: list[DepartureCity] = field(default_factory=list)
    departure_city_airports: dict[str, str] = field(default_factory=dict)  # city -> airport
    rules_meta: RulesMeta = field(
        default_factory=lambda: RulesMeta(
            min_nights=3,
            max_nights=10,
            min_nights_per_city=2,
            first_night="2027-04-01",
            last_departure="2027-04-20",
        )
    )
    max_flight_seats: int = 9


def build_indexes(
    airports: list[Airport],
    flights: list[Flight],
    hotels: list[Hotel],
    rooms: list[RoomType],
    availability: list[RoomAvailability],
    transfers: list[Transfer],
    attractions: list[Attraction],
    countries: list[Country],
    departure_cities: list[DepartureCity],
    links: list[IntercityLink],
    rules_meta: RulesMeta,
) -> CatalogIndexes:
    """Build all lookup dictionaries from the raw catalog collections."""
    idx = CatalogIndexes(rules_meta=rules_meta)

    # Airports
    for a in airports:
        idx.airports_by_code[a.code] = a
        idx.airports_by_city[a.city].append(a)
        for served_city in a.serves_cities:
            idx.airports_serving_city[served_city].append(a)

    # Flights
    max_seats = 0
    for f in flights:
        idx.flights_by_id[f.flight_id] = f
        idx.flights_by_from_and_arr_date[(f.from_airport, f.arrival_date)].append(f)
        idx.flights_by_to_and_dep_date[(f.to_airport, f.departure_date)].append(f)
        if f.seats_left > max_seats:
            max_seats = f.seats_left
    idx.max_flight_seats = max_seats or 9

    # Hotels
    for h in hotels:
        idx.hotels_by_id[h.hotel_id] = h
        idx.hotels_by_city[h.city].append(h)

    # Rooms
    for r in rooms:
        idx.rooms_by_id[r.room_id] = r
        idx.rooms_by_hotel[r.hotel_id].append(r)

    # Availability
    for av in availability:
        idx.availability[(av.room_id, av.date)] = av.rooms_left

    # Transfers
    for t in transfers:
        idx.transfers_by_id[t.transfer_id] = t
        if t.airport_code and t.city:
            idx.airport_transfers_by_airport_city[(t.airport_code, t.city)].append(t)
        if t.from_city and t.to_city:
            idx.intercity_transfers_by_route[(t.from_city, t.to_city)].append(t)

    # Intercity links
    for l in links:
        idx.link_transfer_ids[(l.from_city, l.to_city)].extend(l.transfer_ids)

    # Attractions. Nara's 2 are indexed too (by_id lets the validator reject them by ID), but the builder
    # only looks up cities that have hotels, so attractions_by_city["Nara"] is never offered.
    for att in attractions:
        idx.attractions_by_id[att.attraction_id] = att
        idx.attractions_by_city[att.city].append(att)

    # Countries & departure cities
    for c in countries:
        idx.countries_by_name[c.name] = c
        idx.countries_by_code[c.code] = c

    idx.departure_cities = departure_cities
    for dc in departure_cities:
        idx.departure_city_airports[dc.city] = dc.airport

    return idx

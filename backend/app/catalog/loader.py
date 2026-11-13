"""Catalog loader: reads MySQL catalog tables into domain models and indexes at startup.

Includes a JSON fallback for running tests and offline development without MySQL.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.catalog.indexes import CatalogIndexes, build_indexes
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
from app.core.config import get_settings
from app.core.database import db_ping, get_engine

log = logging.getLogger(__name__)


def _to_json_list(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return []
    return []


def _iso_str(val: Any) -> str:
    if val is None:
        return ""
    # Could be datetime or str
    s = str(val).replace(" ", "T")
    return s


def load_from_db(conn: Connection) -> CatalogIndexes:
    """Read MySQL catalog tables into models and build indexes."""
    # 1. Airports and served cities
    city_airports: dict[str, list[str]] = {}
    for r in conn.execute(text("SELECT airport_code, city_name FROM city_airport")).mappings():
        city_airports.setdefault(r["airport_code"], []).append(r["city_name"])

    airports: list[Airport] = []
    for r in conn.execute(text("SELECT code, name, city, country, timezone, lat, lng FROM airport")).mappings():
        airports.append(
            Airport(
                code=r["code"],
                name=r["name"],
                city=r["city"],
                country=r["country"],
                timezone=r["timezone"],
                lat=float(r["lat"]) if r["lat"] is not None else None,
                lng=float(r["lng"]) if r["lng"] is not None else None,
                serves_cities=city_airports.get(r["code"], []),
            )
        )

    # 2. Flights
    flights: list[Flight] = []
    flight_sql = """
        SELECT flight_id, airline, flight_number, from_airport, to_airport,
               departure_local, arrival_local, stops, duration_minutes,
               price_per_seat, seats_left, cabin
        FROM flight
    """
    for r in conn.execute(text(flight_sql)).mappings():
        flights.append(
            Flight(
                flight_id=r["flight_id"],
                airline=r["airline"],
                flight_number=r["flight_number"],
                from_airport=r["from_airport"],
                to_airport=r["to_airport"],
                departure_local=_iso_str(r["departure_local"]),
                arrival_local=_iso_str(r["arrival_local"]),
                stops=int(r["stops"]),
                duration_minutes=int(r["duration_minutes"]),
                price_per_seat=int(r["price_per_seat"]),
                seats_left=int(r["seats_left"]),
                cabin=r["cabin"],
            )
        )

    # 3. Hotels
    hotels: list[Hotel] = []
    hotel_sql = """
        SELECT hotel_id, name, aliases, city, area, lat, lng, stars, rating,
               check_in_from, check_out_until, family_friendly, image
        FROM hotel
    """
    for r in conn.execute(text(hotel_sql)).mappings():
        hotels.append(
            Hotel(
                hotel_id=r["hotel_id"],
                name=r["name"],
                aliases=_to_json_list(r["aliases"]),
                city=r["city"],
                area=r["area"],
                lat=float(r["lat"]) if r["lat"] is not None else None,
                lng=float(r["lng"]) if r["lng"] is not None else None,
                stars=int(r["stars"]),
                rating=float(r["rating"]),
                check_in_from=str(r["check_in_from"]),
                check_out_until=str(r["check_out_until"]),
                family_friendly=bool(r["family_friendly"]),
                image=r["image"],
            )
        )

    # 4. Rooms
    rooms: list[RoomType] = []
    room_sql = """
        SELECT room_id, hotel_id, room_type, name, max_adults, max_children,
               price_per_night, refundable
        FROM room
    """
    for r in conn.execute(text(room_sql)).mappings():
        rooms.append(
            RoomType(
                room_id=r["room_id"],
                hotel_id=r["hotel_id"],
                room_type=r["room_type"],
                name=r["name"],
                max_adults=int(r["max_adults"]),
                max_children=int(r["max_children"]),
                price_per_night=int(r["price_per_night"]),
                refundable=bool(r["refundable"]),
            )
        )

    # 5. Availability
    avail: list[RoomAvailability] = []
    for r in conn.execute(text("SELECT room_id, date, rooms_left FROM room_availability")).mappings():
        avail.append(
            RoomAvailability(
                room_id=r["room_id"],
                date=str(r["date"]),
                rooms_left=int(r["rooms_left"]),
            )
        )

    # 6. Transfers (with subtypes)
    transfers: list[Transfer] = []
    transfer_sql = """
        SELECT t.transfer_id, t.type, t.name, t.from_point, t.to_point,
               t.max_passengers, t.service_from, t.service_until, t.duration_minutes,
               t.pricing, t.price, t.child_price,
               at.airport_code, COALESCE(at.city, ct.city) AS city, at.area,
               it.from_city, it.to_city, it.frequency_minutes, it.door_to_door
        FROM transfer t
        LEFT JOIN airport_transfer at ON t.transfer_id = at.transfer_id
        LEFT JOIN city_transfer ct ON t.transfer_id = ct.transfer_id
        LEFT JOIN intercity_transfer it ON t.transfer_id = it.transfer_id
    """
    for r in conn.execute(text(transfer_sql)).mappings():
        transfers.append(
            Transfer(
                transfer_id=r["transfer_id"],
                type=r["type"],
                name=r["name"],
                from_point=r["from_point"],
                to_point=r["to_point"],
                max_passengers=int(r["max_passengers"]),
                service_from=str(r["service_from"]),
                service_until=str(r["service_until"]),
                duration_minutes=int(r["duration_minutes"]),
                pricing=r["pricing"],
                price=int(r["price"]),
                child_price=int(r["child_price"]) if r["child_price"] is not None else None,
                airport_code=r["airport_code"],
                city=r["city"],
                area=r["area"],
                from_city=r["from_city"],
                to_city=r["to_city"],
                frequency_minutes=int(r["frequency_minutes"]) if r["frequency_minutes"] is not None else None,
                door_to_door=bool(r["door_to_door"]) if r["door_to_door"] is not None else None,
            )
        )

    # 7. Attractions
    attractions: list[Attraction] = []
    attraction_sql = """
        SELECT attraction_id, name, name_ja, city, category, lat, lng,
               open_days, open_from, open_until, closed_dates, aliases,
               visit_minutes, child_friendly, `accessible`, price_per_person,
               child_price, image
        FROM attraction
    """
    for r in conn.execute(text(attraction_sql)).mappings():
        attractions.append(
            Attraction(
                attraction_id=r["attraction_id"],
                name=r["name"],
                name_ja=r["name_ja"],
                city=r["city"],
                category=r["category"],
                lat=float(r["lat"]) if r["lat"] is not None else None,
                lng=float(r["lng"]) if r["lng"] is not None else None,
                open_days=_to_json_list(r["open_days"]),
                open_from=str(r["open_from"]),
                open_until=str(r["open_until"]),
                closed_dates=_to_json_list(r["closed_dates"]),
                aliases=_to_json_list(r["aliases"]),
                visit_minutes=int(r["visit_minutes"]),
                child_friendly=bool(r["child_friendly"]),
                accessible=bool(r["accessible"]),
                price_per_person=int(r["price_per_person"]),
                child_price=int(r["child_price"]) if r["child_price"] is not None else None,
                image=r["image"],
            )
        )

    # 8. Geography & Rules
    country_cities: dict[str, list[str]] = {}
    for r in conn.execute(text("SELECT country_code, name FROM destination_city")).mappings():
        country_cities.setdefault(r["country_code"], []).append(r["name"])

    countries: list[Country] = []
    for r in conn.execute(text("SELECT code, name, timezone FROM country")).mappings():
        countries.append(
            Country(
                code=r["code"],
                name=r["name"],
                timezone=r["timezone"],
                cities=country_cities.get(r["code"], []),
            )
        )

    dep_cities: list[DepartureCity] = []
    for r in conn.execute(text("SELECT city, airport_code FROM departure_city")).mappings():
        dep_cities.append(DepartureCity(city=r["city"], airport=r["airport_code"]))

    link_map: dict[tuple[str, str, str], list[str]] = {}
    for r in conn.execute(text("SELECT country_code, from_city, to_city, transfer_id FROM link_transfer")).mappings():
        link_map.setdefault((r["country_code"], r["from_city"], r["to_city"]), []).append(r["transfer_id"])

    links = [
        IntercityLink(country_code=cc, from_city=fc, to_city=tc, transfer_ids=tids)
        for (cc, fc, tc), tids in link_map.items()
    ]

    meta_row = conn.execute(text("SELECT meta_value FROM catalog_meta WHERE meta_key = 'rules'")).first()
    rules_dict = json.loads(meta_row[0]) if meta_row else {}
    dw = rules_dict.get("data_window", {})
    rules_meta = RulesMeta(
        min_nights=rules_dict.get("min_nights", 3),
        max_nights=rules_dict.get("max_nights", 10),
        min_nights_per_city=rules_dict.get("min_nights_per_city", 2),
        first_night=dw.get("first_night", "2027-04-01"),
        last_departure=dw.get("last_departure", "2027-04-20"),
    )

    return build_indexes(
        airports=airports,
        flights=flights,
        hotels=hotels,
        rooms=rooms,
        availability=avail,
        transfers=transfers,
        attractions=attractions,
        countries=countries,
        departure_cities=dep_cities,
        links=links,
        rules_meta=rules_meta,
    )


def load_from_json(catalog_dir: Path) -> CatalogIndexes:
    """Read raw JSON catalog files into models and build indexes (fallback & offline test mode)."""
    def _read_json(filename: str):
        return json.loads((catalog_dir / filename).read_text(encoding="utf-8"))

    dest = _read_json("destinations.json")
    airports_raw = _read_json("airports.json")
    flights_raw = _read_json("flights.json")
    hotels_raw = _read_json("hotels.json")
    rooms_raw = _read_json("rooms.json")
    avail_raw = _read_json("availability.json")
    transfers_raw = _read_json("transfers.json")
    attractions_raw = _read_json("attractions.json")

    airports = [
        Airport(
            code=a["code"],
            name=a["name"],
            city=a["city"],
            country=a["country"],
            timezone=a["timezone"],
            lat=a.get("lat"),
            lng=a.get("lng"),
            serves_cities=a.get("serves_cities") or [],
        )
        for a in airports_raw
    ]

    flights = [
        Flight(
            flight_id=f["flight_id"],
            airline=f["airline"],
            flight_number=f["flight_number"],
            from_airport=f["from"],
            to_airport=f["to"],
            departure_local=_iso_str(f["departure_local"]),
            arrival_local=_iso_str(f["arrival_local"]),
            stops=f["stops"],
            duration_minutes=f["duration_minutes"],
            price_per_seat=int(f["price_per_seat"]["amount"]),
            seats_left=f["seats_left"],
            cabin=f["cabin"],
        )
        for f in flights_raw
    ]

    hotels = [
        Hotel(
            hotel_id=h["hotel_id"],
            name=h["name"],
            aliases=h.get("aliases", []),
            city=h["city"],
            area=h["area"],
            lat=h.get("lat"),
            lng=h.get("lng"),
            stars=h["stars"],
            rating=float(h["rating"]),
            check_in_from=h["check_in_from"],
            check_out_until=h["check_out_until"],
            family_friendly=h["family_friendly"],
            image=h.get("image"),
        )
        for h in hotels_raw
    ]

    rooms = [
        RoomType(
            room_id=r["room_id"],
            hotel_id=r["hotel_id"],
            room_type=r["room_type"],
            name=r["name"],
            max_adults=r["max_adults"],
            max_children=r["max_children"],
            price_per_night=int(r["price_per_night"]["amount"]),
            refundable=r["refundable"],
        )
        for r in rooms_raw
    ]

    avail = [
        RoomAvailability(
            room_id=av["room_id"],
            date=av["date"],
            rooms_left=av["rooms_left"],
        )
        for av in avail_raw
    ]

    transfers = [
        Transfer(
            transfer_id=t["transfer_id"],
            type=t["type"],
            name=t["name"],
            from_point=t["from_point"],
            to_point=t["to_point"],
            max_passengers=t["max_passengers"],
            service_from=t["service_from"],
            service_until=t["service_until"],
            duration_minutes=t["duration_minutes"],
            pricing=t["pricing"],
            price=int(t["price"]["amount"]),
            child_price=int(t["child_price"]["amount"]) if t.get("child_price") is not None else None,
            airport_code=t.get("airport"),
            city=t.get("city"),
            area=t.get("area"),
            from_city=t.get("from_city"),
            to_city=t.get("to_city"),
            frequency_minutes=t.get("frequency_minutes"),
            door_to_door=t.get("door_to_door"),
        )
        for t in transfers_raw
    ]

    attractions = [
        Attraction(
            attraction_id=a["attraction_id"],
            name=a["name"],
            name_ja=a.get("name_ja"),
            city=a["city"],
            category=a["category"],
            lat=a.get("lat"),
            lng=a.get("lng"),
            open_days=a["open_days"],
            open_from=a["open_from"],
            open_until=a["open_until"],
            closed_dates=a.get("closed_dates", []),
            aliases=a.get("aliases", []),
            visit_minutes=a["visit_minutes"],
            child_friendly=a["child_friendly"],
            accessible=a["accessible"],
            price_per_person=int(a["price_per_person"]["amount"]),
            child_price=int(a["child_price"]["amount"]) if a.get("child_price") is not None else None,
            image=a.get("image"),
        )
        for a in attractions_raw
    ]

    countries = [
        Country(
            code=c["code"],
            name=c["name"],
            timezone=c["timezone"],
            cities=[ct["name"] for ct in c["cities"]],
        )
        for c in dest["countries"]
    ]

    dep_cities = [
        DepartureCity(city=d["city"], airport=d["airport"])
        for d in dest["departure_cities"]
    ]

    links = []
    for c in dest["countries"]:
        for link in c.get("links", []):
            links.append(
                IntercityLink(
                    country_code=c["code"],
                    from_city=link["from_city"],
                    to_city=link["to_city"],
                    transfer_ids=link["transfer_ids"],
                )
            )

    rules_dict = dest.get("rules", {})
    dw = rules_dict.get("data_window", {})
    rules_meta = RulesMeta(
        min_nights=rules_dict.get("min_nights", 3),
        max_nights=rules_dict.get("max_nights", 10),
        min_nights_per_city=rules_dict.get("min_nights_per_city", 2),
        first_night=dw.get("first_night", "2027-04-01"),
        last_departure=dw.get("last_departure", "2027-04-20"),
    )

    return build_indexes(
        airports=airports,
        flights=flights,
        hotels=hotels,
        rooms=rooms,
        availability=avail,
        transfers=transfers,
        attractions=attractions,
        countries=countries,
        departure_cities=dep_cities,
        links=links,
        rules_meta=rules_meta,
    )


LAST_SOURCE: str | None = None   # "mysql" or "json": where the last load_catalog() read from


def load_catalog() -> CatalogIndexes:
    """Load the catalog from MySQL if available and DB_AUTO_INIT is enabled; otherwise fall back to raw JSON files."""
    global LAST_SOURCE
    settings = get_settings()
    if settings.DB_AUTO_INIT and db_ping():
        try:
            with get_engine().connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM flight")).scalar() or 0
                if count > 0:
                    log.info("Loading catalog from MySQL database...")
                    LAST_SOURCE = "mysql"
                    return load_from_db(conn)
        except Exception:
            log.exception("Failed to load catalog from MySQL; falling back to JSON.")

    log.info("Loading catalog from JSON files in %s...", settings.catalog_dir)
    LAST_SOURCE = "json"
    return load_from_json(settings.catalog_dir)

"""
In-memory indexing for the Build My Holiday travel catalogue.

Builds efficient lookup structures from raw catalogue datasets without mutating
records or performing full-array scans on hot paths.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional


class CatalogIndexes:
    """
    In-memory indexing engine for travel catalogue data.
    Provides O(1) dictionary-based lookups and precomputed groupings.
    """

    def __init__(
        self,
        destinations: dict[str, Any],
        airports: list[dict[str, Any]],
        flights: list[dict[str, Any]],
        hotels: list[dict[str, Any]],
        rooms: list[dict[str, Any]],
        availability: list[dict[str, Any]],
        transfers: list[dict[str, Any]],
        attractions: list[dict[str, Any]],
    ) -> None:
        self._destinations = destinations
        self._airports = airports
        self._flights = flights
        self._hotels = hotels
        self._rooms = rooms
        self._availability = availability
        self._transfers = transfers
        self._attractions = attractions

        # Build indexes
        self._build_indexes()

    def _build_indexes(self) -> None:
        """Construct all index dictionaries."""

        # 1. Airports by airport code
        self.airport_by_code: dict[str, dict[str, Any]] = {
            a["code"]: a for a in self._airports if "code" in a
        }

        # 2. Destination cities and their associated airports
        # Kyoto -> ["KIX"], Tokyo -> ["NRT", "HND"], etc.
        self.airports_by_destination_city: dict[str, list[str]] = defaultdict(list)
        self.destination_cities_by_airport: dict[str, list[str]] = defaultdict(list)
        self.country_by_city: dict[str, dict[str, Any]] = {}
        self.rules: dict[str, Any] = self._destinations.get("rules", {})

        for country in self._destinations.get("countries", []):
            country_info = {
                "code": country.get("code"),
                "name": country.get("name"),
                "timezone": country.get("timezone"),
            }
            for city in country.get("cities", []):
                city_name = city.get("name")
                city_airports = list(city.get("airports", []))
                if city_name:
                    self.airports_by_destination_city[city_name] = city_airports
                    self.country_by_city[city_name] = country_info
                    for ap in city_airports:
                        if city_name not in self.destination_cities_by_airport[ap]:
                            self.destination_cities_by_airport[ap].append(city_name)

        # Cross-check serves_cities from airports.json as well
        for a in self._airports:
            ap_code = a.get("code")
            serves = a.get("serves_cities") or []
            for sc in serves:
                if sc and ap_code and sc in self.airports_by_destination_city:
                    if ap_code not in self.airports_by_destination_city[sc]:
                        self.airports_by_destination_city[sc].append(ap_code)
                if sc and ap_code and sc not in self.destination_cities_by_airport[ap_code]:
                    self.destination_cities_by_airport[ap_code].append(sc)

        # 3. Departure cities and their airport codes
        self.departure_cities: list[dict[str, str]] = list(
            self._destinations.get("departure_cities", [])
        )
        self.departure_city_to_airport: dict[str, str] = {}
        self.departure_airport_to_city: dict[str, str] = {}
        for dep in self.departure_cities:
            city = dep.get("city")
            airport = dep.get("airport")
            if city and airport:
                self.departure_city_to_airport[city] = airport
                self.departure_airport_to_city[airport] = city

        # 4. Flights indexes
        # By flight_id
        self.flight_by_id: dict[str, dict[str, Any]] = {
            f["flight_id"]: f for f in self._flights if "flight_id" in f
        }
        # By (origin, destination) route
        self.flights_by_route: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        # By (origin, destination, arrival_date)
        self.flights_by_route_and_arrival_date: dict[tuple[str, str, str], list[dict[str, Any]]] = (
            defaultdict(list)
        )
        # By (origin, destination, departure_date)
        self.flights_by_route_and_departure_date: dict[tuple[str, str, str], list[dict[str, Any]]] = (
            defaultdict(list)
        )

        for fl in self._flights:
            orig = fl.get("from")
            dest = fl.get("to")
            if orig and dest:
                route = (orig, dest)
                self.flights_by_route[route].append(fl)

                arr_local = fl.get("arrival_local", "")
                if arr_local:
                    arr_date = arr_local.split("T")[0]
                    self.flights_by_route_and_arrival_date[(orig, dest, arr_date)].append(fl)

                dep_local = fl.get("departure_local", "")
                if dep_local:
                    dep_date = dep_local.split("T")[0]
                    self.flights_by_route_and_departure_date[(orig, dest, dep_date)].append(fl)

        # 5. Hotels indexes
        # By hotel_id
        self.hotel_by_id: dict[str, dict[str, Any]] = {
            h["hotel_id"]: h for h in self._hotels if "hotel_id" in h
        }
        # By city
        self.hotels_by_city: dict[str, list[dict[str, Any]]] = defaultdict(list)
        # By (city, area)
        self.hotels_by_city_and_area: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

        for h in self._hotels:
            city = h.get("city")
            area = h.get("area")
            if city:
                self.hotels_by_city[city].append(h)
                if area:
                    self.hotels_by_city_and_area[(city, area)].append(h)

        # 6. Rooms indexes
        # By room_id
        self.room_by_id: dict[str, dict[str, Any]] = {
            r["room_id"]: r for r in self._rooms if "room_id" in r
        }
        # By hotel_id
        self.rooms_by_hotel_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in self._rooms:
            hid = r.get("hotel_id")
            if hid:
                self.rooms_by_hotel_id[hid].append(r)

        # 7. Availability indexes
        # By (room_id, date) -> full availability record
        self.availability_by_room_and_date: dict[tuple[str, str], dict[str, Any]] = {}
        # By (room_id, date) -> rooms_left (integer)
        self.rooms_left_by_room_and_date: dict[tuple[str, str], int] = {}
        # By room_id -> {date: rooms_left}
        self.availability_by_room: dict[str, dict[str, int]] = defaultdict(dict)

        for av in self._availability:
            rid = av.get("room_id")
            dt = av.get("date")
            r_left = av.get("rooms_left", 0)
            if rid and dt:
                key = (rid, dt)
                self.availability_by_room_and_date[key] = av
                self.rooms_left_by_room_and_date[key] = r_left
                self.availability_by_room[rid][dt] = r_left

        # 8. Transfers indexes
        # By transfer_id
        self.transfer_by_id: dict[str, dict[str, Any]] = {
            t["transfer_id"]: t for t in self._transfers if "transfer_id" in t
        }
        # By city-to-city route: (from_city, to_city)
        # Do not assume routes are bidirectional.
        self.transfers_by_city_route: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        # Airport transfers by airport code
        self.transfers_by_airport: dict[str, list[dict[str, Any]]] = defaultdict(list)
        # Airport transfers by (airport, city)
        self.transfers_by_airport_and_city: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

        for t in self._transfers:
            fc = t.get("from_city")
            tc = t.get("to_city")
            if fc and tc:
                self.transfers_by_city_route[(fc, tc)].append(t)

            ap = t.get("airport")
            ct = t.get("city")
            if ap:
                self.transfers_by_airport[ap].append(t)
                if ct:
                    self.transfers_by_airport_and_city[(ap, ct)].append(t)

        # 9. Attractions indexes
        # By attraction_id
        self.attraction_by_id: dict[str, dict[str, Any]] = {
            att["attraction_id"]: att for att in self._attractions if "attraction_id" in att
        }
        # By city
        self.attractions_by_city: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for att in self._attractions:
            ct = att.get("city")
            if ct:
                self.attractions_by_city[ct].append(att)

    # --------------------------------------------------------------------------
    # Convenient accessor methods
    # --------------------------------------------------------------------------

    def get_airport(self, code: str) -> Optional[dict[str, Any]]:
        """Look up airport by 3-letter IATA code."""
        return self.airport_by_code.get(code.upper())

    def get_flights(self, origin: str, destination: str) -> list[dict[str, Any]]:
        """Return all flights for an origin-destination route."""
        return list(self.flights_by_route.get((origin.upper(), destination.upper()), []))

    def get_flights_by_arrival_date(
        self, origin: str, destination: str, arrival_date: str
    ) -> list[dict[str, Any]]:
        """Return flights on route arriving on a specific date (YYYY-MM-DD)."""
        return list(
            self.flights_by_route_and_arrival_date.get(
                (origin.upper(), destination.upper(), arrival_date), []
            )
        )

    def get_flights_by_departure_date(
        self, origin: str, destination: str, departure_date: str
    ) -> list[dict[str, Any]]:
        """Return flights on route departing on a specific date (YYYY-MM-DD)."""
        return list(
            self.flights_by_route_and_departure_date.get(
                (origin.upper(), destination.upper(), departure_date), []
            )
        )

    def get_flight(self, flight_id: str) -> Optional[dict[str, Any]]:
        """Look up flight by unique flight_id."""
        return self.flight_by_id.get(flight_id)

    def get_hotels_by_city(self, city: str) -> list[dict[str, Any]]:
        """Return all hotels in a destination city."""
        return list(self.hotels_by_city.get(city, []))

    def get_hotels_by_city_and_area(self, city: str, area: str) -> list[dict[str, Any]]:
        """Return hotels located in a specific area of a city."""
        return list(self.hotels_by_city_and_area.get((city, area), []))

    def get_hotel(self, hotel_id: str) -> Optional[dict[str, Any]]:
        """Look up hotel by hotel_id."""
        return self.hotel_by_id.get(hotel_id)

    def get_rooms_by_hotel(self, hotel_id: str) -> list[dict[str, Any]]:
        """Return all room types for a hotel."""
        return list(self.rooms_by_hotel_id.get(hotel_id, []))

    def get_room(self, room_id: str) -> Optional[dict[str, Any]]:
        """Look up room by room_id."""
        return self.room_by_id.get(room_id)

    def get_availability(self, room_id: str, date: str) -> Optional[dict[str, Any]]:
        """Look up availability record for a room on a given night."""
        return self.availability_by_room_and_date.get((room_id, date))

    def get_rooms_left(self, room_id: str, date: str) -> Optional[int]:
        """Return number of free rooms of room_id on date, or None if no record exists."""
        return self.rooms_left_by_room_and_date.get((room_id, date))

    def check_room_availability(
        self, room_id: str, dates: list[str], required_rooms: int = 1
    ) -> bool:
        """Verify that room_id has at least required_rooms available on all specified nights."""
        for dt in dates:
            left = self.get_rooms_left(room_id, dt)
            if left is None or left < required_rooms:
                return False
        return True

    def get_transfer(self, transfer_id: str) -> Optional[dict[str, Any]]:
        """Look up transfer service by transfer_id."""
        return self.transfer_by_id.get(transfer_id)

    def get_transfers_by_route(self, from_city: str, to_city: str) -> list[dict[str, Any]]:
        """Return transfer options between two cities (one-way)."""
        return list(self.transfers_by_city_route.get((from_city, to_city), []))

    def get_airport_transfers(
        self, airport: str, city: Optional[str] = None, area: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Return airport transfers for an airport, optionally filtered by city and area.
        Transfers with area=None serve all areas of that city.
        """
        results = self.transfers_by_airport.get(airport.upper(), [])
        if city is not None:
            results = [t for t in results if t.get("city") == city]
        if area is not None:
            results = [
                t for t in results if t.get("area") is None or t.get("area") == area
            ]
        return list(results)

    def get_attractions_by_city(self, city: str) -> list[dict[str, Any]]:
        """Return all attractions in a city."""
        return list(self.attractions_by_city.get(city, []))

    def get_attraction(self, attraction_id: str) -> Optional[dict[str, Any]]:
        """Look up attraction by attraction_id."""
        return self.attraction_by_id.get(attraction_id)

    def get_airports_for_destination_city(self, city: str) -> list[str]:
        """Return list of airport codes serving a destination city."""
        return list(self.airports_by_destination_city.get(city, []))

    def get_cities_served_by_airport(self, airport_code: str) -> list[str]:
        """Return destination cities reachable from an airport."""
        return list(self.destination_cities_by_airport.get(airport_code.upper(), []))

    def get_departure_airport(self, departure_city: str) -> Optional[str]:
        """Return airport code for a departure city (e.g. 'Bengaluru' -> 'BLR')."""
        return self.departure_city_to_airport.get(departure_city)

    def get_departure_city(self, airport_code: str) -> Optional[str]:
        """Return departure city name for an airport code (e.g. 'BLR' -> 'Bengaluru')."""
        return self.departure_airport_to_city.get(airport_code.upper())

    def get_country_for_city(self, city_name: str) -> Optional[dict[str, Any]]:
        """Return country information for a destination city."""
        return self.country_by_city.get(city_name)

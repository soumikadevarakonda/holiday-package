"""CatalogStore singleton: in-memory catalog store, lookup indexes, and query helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.catalog.indexes import CatalogIndexes
    from app.catalog.models import (
        Airport,
        Attraction,
        Country,
        Flight,
        Hotel,
        RoomType,
        RulesMeta,
        Transfer,
    )

log = logging.getLogger(__name__)


class CatalogStore:
    def __init__(self) -> None:
        self.loaded: bool = False
        self.source: str | None = None      # "mysql", "json" or "injected"
        self._indexes: CatalogIndexes | None = None

    @property
    def indexes(self) -> CatalogIndexes:
        if not self.loaded or self._indexes is None:
            self.load()
        assert self._indexes is not None
        return self._indexes

    def load(self, indexes: CatalogIndexes | None = None) -> None:
        """Load catalog into store. If indexes is not passed, loads via loader."""
        if indexes is not None:
            self._indexes = indexes
            self.source = "injected"
        else:
            from app.catalog import loader

            self._indexes = loader.load_catalog()
            self.source = loader.LAST_SOURCE
        self.loaded = True
        # cached hotel searches belong to the previous catalog
        from app.builder.hotels import clear_cache

        clear_cache()
        log.info(
            "CatalogStore loaded with %d flights, %d hotels, %d attractions",
            len(self._indexes.flights_by_id),
            len(self._indexes.hotels_by_id),
            len(self._indexes.attractions_by_id),
        )

    # -------------------------------------------------------- Query Helpers

    def get_airport(self, code: str) -> Airport | None:
        return self.indexes.airports_by_code.get(code)

    def get_flight(self, flight_id: str) -> Flight | None:
        return self.indexes.flights_by_id.get(flight_id)

    def get_hotel(self, hotel_id: str) -> Hotel | None:
        return self.indexes.hotels_by_id.get(hotel_id)

    def get_room(self, room_id: str) -> RoomType | None:
        return self.indexes.rooms_by_id.get(room_id)

    def get_transfer(self, transfer_id: str) -> Transfer | None:
        return self.indexes.transfers_by_id.get(transfer_id)

    def get_attraction(self, attraction_id: str) -> Attraction | None:
        return self.indexes.attractions_by_id.get(attraction_id)

    def get_country(self, name_or_code: str) -> Country | None:
        return self.indexes.countries_by_name.get(name_or_code) or self.indexes.countries_by_code.get(name_or_code)

    def get_rooms_left(self, room_id: str, stay_date: str) -> int:
        return self.indexes.availability.get((room_id, stay_date), 0)

    def get_arrival_flights(self, from_airport: str, arr_date: str) -> list[Flight]:
        return self.indexes.flights_by_from_and_arr_date.get((from_airport, arr_date), [])

    def get_return_flights(self, to_airport: str, dep_date: str) -> list[Flight]:
        return self.indexes.flights_by_to_and_dep_date.get((to_airport, dep_date), [])

    def get_airports_for_city(self, city: str) -> list[Airport]:
        return self.indexes.airports_serving_city.get(city, [])

    def get_hotels_in_city(self, city: str) -> list[Hotel]:
        return self.indexes.hotels_by_city.get(city, [])

    def get_rooms_for_hotel(self, hotel_id: str) -> list[RoomType]:
        return self.indexes.rooms_by_hotel.get(hotel_id, [])

    def get_airport_transfers(self, airport_code: str, city: str) -> list[Transfer]:
        return self.indexes.airport_transfers_by_airport_city.get((airport_code, city), [])

    def get_intercity_transfers(self, from_city: str, to_city: str) -> list[Transfer]:
        return self.indexes.intercity_transfers_by_route.get((from_city, to_city), [])

    def get_attractions_in_city(self, city: str) -> list[Attraction]:
        return self.indexes.attractions_by_city.get(city, [])

    @property
    def rules(self) -> RulesMeta:
        return self.indexes.rules_meta

    @property
    def max_flight_seats(self) -> int:
        return self.indexes.max_flight_seats


_store = CatalogStore()


def get_store() -> CatalogStore:
    return _store

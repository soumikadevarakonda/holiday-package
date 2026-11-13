"""Parse a Package once into the facts every rule check needs (shared by rules/checks/*).

The checks never re-read the package format: they use this context plus the catalog store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from app.catalog.models import Attraction, Flight, Hotel, RoomType, Transfer
from app.catalog.store import CatalogStore, get_store
from app.core.package_model import Item, Package, Violation

AIRPORT_TYPES = ("AIRPORT_TAXI", "AIRPORT_BUS", "AIRPORT_VAN")
CITY_TYPES = ("CITY_TAXI", "CITY_BUS")


def parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def parse_d(s: str) -> date:
    return date.fromisoformat(s[:10])


@dataclass
class FlightLeg:
    item: Item
    flight: Flight


@dataclass
class HotelStay:
    item: Item
    hotel: Hotel
    room: RoomType
    check_in: date
    check_out: date

    @property
    def nights(self) -> list[date]:
        return [self.check_in + timedelta(days=i) for i in range((self.check_out - self.check_in).days)]


@dataclass
class TransferUse:
    item: Item
    transfer: Transfer
    start: datetime


@dataclass
class Visit:
    item: Item
    attraction: Attraction
    start: datetime
    end: datetime


@dataclass
class Ctx:
    pkg: Package
    store: CatalogStore
    adults: int
    children: int
    travelers: int
    start: date                      # S
    end: date                        # L (return day)
    nights: int                      # N
    home_airport: str
    country_cities: set[str]
    flights: list[FlightLeg] = field(default_factory=list)          # sorted by departure
    stays: list[HotelStay] = field(default_factory=list)            # sorted by check-in
    airport_transfers: list[TransferUse] = field(default_factory=list)
    intercity_transfers: list[TransferUse] = field(default_factory=list)
    city_transfers: list[TransferUse] = field(default_factory=list)
    visits: list[Visit] = field(default_factory=list)
    errors: list[Violation] = field(default_factory=list)           # unknown IDs / bad formats

    @property
    def arrival(self) -> FlightLeg | None:
        return self.flights[0] if len(self.flights) == 2 else None

    @property
    def ret(self) -> FlightLeg | None:
        return self.flights[-1] if len(self.flights) == 2 else None

    def city_of_night(self, d: date) -> str | None:
        for s in self.stays:
            if s.check_in <= d < s.check_out:
                return s.hotel.city
        return None

    @property
    def change_days(self) -> list[date]:
        """Days the traveler moves city: every check-in after the first."""
        return [s.check_in for s in self.stays[1:]]


def build_context(pkg: Package, store: CatalogStore | None = None) -> Ctx:
    store = store or get_store()
    t = pkg.traveler
    start, end = parse_d(pkg.start_date), parse_d(pkg.end_date)
    country = store.get_country(pkg.country)
    ctx = Ctx(pkg=pkg, store=store, adults=t.adults, children=len(t.child_ages),
              travelers=t.adults + len(t.child_ages), start=start, end=end, nights=(end - start).days,
              home_airport=t.home_airport, country_cities=set(country.cities) if country else set())
    if country is None:
        ctx.errors.append(Violation("D2", None, f"Unknown destination country '{pkg.country}'."))

    def unknown(item: Item, what: str) -> None:
        ctx.errors.append(Violation("P1", item.item_id, f"{item.name}: unknown {what} '{item.catalog_id}'."))

    for it in pkg.items:
        try:
            if it.type == "flight":
                f = store.get_flight(it.catalog_id)
                ctx.flights.append(FlightLeg(it, f)) if f else unknown(it, "flight")
            elif it.type == "hotel":
                h, r = store.get_hotel(it.catalog_id), store.get_room(it.room_id or "")
                if not h:
                    unknown(it, "hotel")
                elif not r or r.hotel_id != h.hotel_id:
                    ctx.errors.append(Violation("H2", it.item_id,
                                                f"{it.name}: room '{it.room_id}' is not a room type of this hotel."))
                else:
                    ctx.stays.append(HotelStay(it, h, r, parse_d(it.start), parse_d(it.end or it.start)))
            elif it.type == "transfer":
                tr = store.get_transfer(it.catalog_id)
                if not tr:
                    unknown(it, "transfer")
                    continue
                use = TransferUse(it, tr, parse_dt(it.start))
                if tr.type in AIRPORT_TYPES:
                    ctx.airport_transfers.append(use)
                elif tr.type in CITY_TYPES:
                    ctx.city_transfers.append(use)
                else:
                    ctx.intercity_transfers.append(use)
            elif it.type == "attraction":
                a = store.get_attraction(it.catalog_id)
                if not a:
                    unknown(it, "attraction")
                    continue
                s = parse_dt(it.start)
                ctx.visits.append(Visit(it, a, s, s + timedelta(minutes=a.visit_minutes)))
        except (ValueError, TypeError) as exc:
            ctx.errors.append(Violation("P1", it.item_id, f"{it.name}: bad date or time ({exc})."))

    ctx.flights.sort(key=lambda x: x.flight.departure_local)
    ctx.stays.sort(key=lambda x: x.check_in)
    ctx.airport_transfers.sort(key=lambda x: x.start)
    ctx.intercity_transfers.sort(key=lambda x: x.start)
    ctx.visits.sort(key=lambda x: x.start)
    return ctx

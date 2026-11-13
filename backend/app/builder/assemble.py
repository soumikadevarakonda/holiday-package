"""Turn chosen parts into a Package (shared trip format items, in time order)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.builder.attractions import VisitChoice
from app.builder.hotels import StayOption
from app.builder.transfers import TransferChoice
from app.catalog.models import Flight
from app.core.package_model import CityStay, Item, Package, Traveler, TripRequest
from app.core.timeutil import format_iso_hm
from app.pricing.calculator import calculate_flight_price


@dataclass
class Parts:
    plan: list[CityStay]
    arrival: Flight
    arrival_transfer: TransferChoice
    stays: list[StayOption]
    intercity: list[TransferChoice]
    visits: list[VisitChoice]
    return_transfer: TransferChoice
    ret: Flight

    @property
    def travel_minutes(self) -> int:
        """G4 'fastest': both flights + inter-city transfers."""
        return (self.arrival.duration_minutes + self.ret.duration_minutes
                + sum(t.transfer.duration_minutes for t in self.intercity))

    @property
    def avg_stars(self) -> float:
        """G4 'best rated': hotel stars averaged over nights."""
        nights = sum(c.nights for c in self.plan)
        return sum(s.hotel.stars * c.nights for s, c in zip(self.stays, self.plan)) / nights


def trip_id(req: TripRequest) -> str:
    key = f"{req.departure_city}|{req.country}|{req.start_date}|{req.nights}|{req.adults}|{req.children_ages}"
    return "trip-" + hashlib.sha1(key.encode()).hexdigest()[:10]


def assemble(req: TripRequest, home_airport: str, country: str, p: Parts) -> Package:
    T = req.travelers
    rows: list[tuple[datetime, int, dict]] = []   # (sort time, tie-break, item fields)

    def add(when: datetime, order: int, **fields) -> None:
        rows.append((when, order, fields))

    def flight(f: Flight, city: str, order: int) -> None:
        dep = datetime.fromisoformat(f.departure_local)
        add(dep, order, type="flight", name=f"{f.flight_number} {f.from_airport} to {f.to_airport}", city=city,
            catalog_id=f.flight_id, start=format_iso_hm(dep),
            end=format_iso_hm(datetime.fromisoformat(f.arrival_local)),
            quantity=T, price_inr=calculate_flight_price(f.price_per_seat, T))

    def transfer(c: TransferChoice, city: str, order: int) -> None:
        t = c.transfer
        qty = -(-T // t.max_passengers) if t.pricing == "PER_VEHICLE" else T
        add(c.start, order, type="transfer", name=t.name, city=city, catalog_id=t.transfer_id,
            start=format_iso_hm(c.start), end=format_iso_hm(c.end), quantity=qty, price_inr=c.price)

    flight(p.arrival, p.plan[0].city, 0)
    transfer(p.arrival_transfer, p.plan[0].city, 1)
    check_in: date = req.start_date
    for i, (city, stay) in enumerate(zip(p.plan, p.stays)):
        if i > 0:
            transfer(p.intercity[i - 1], city.city, 2)
        check_out = check_in + timedelta(days=city.nights)
        # hotel sorts at 15:00 on check-in day (after arrival / move), date-only in the export
        add(datetime.combine(check_in, datetime.min.time()) + timedelta(hours=15), 3, type="hotel",
            name=stay.hotel.name, city=city.city, catalog_id=stay.hotel.hotel_id, room_id=stay.room.room_id,
            start=check_in.isoformat(), end=check_out.isoformat(), quantity=stay.rooms, price_inr=stay.price)
        check_in = check_out
    for v in p.visits:
        add(v.start, 4, type="attraction", name=v.attraction.name, city=v.attraction.city,
            catalog_id=v.attraction.attraction_id, start=format_iso_hm(v.start), end=format_iso_hm(v.end),
            quantity=T, price_inr=v.price)
    transfer(p.return_transfer, p.plan[-1].city, 5)
    flight(p.ret, req.departure_city, 6)

    rows.sort(key=lambda r: (r[0], r[1]))
    items = [Item(item_id=f"i{n}", **fields) for n, (_, _, fields) in enumerate(rows, start=1)]
    return Package(
        trip_id=trip_id(req),
        traveler=Traveler(name=req.traveler_name, home_airport=home_airport, adults=req.adults,
                          children=req.children, child_ages=list(req.children_ages)),
        start_date=req.start_date.isoformat(),
        end_date=req.end_date.isoformat(),
        country=country,
        budget_inr=req.budget_inr,
        city_plan=[CityStay(c.city, c.nights) for c in p.plan],
        items=items,
    )

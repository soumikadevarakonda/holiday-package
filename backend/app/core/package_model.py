"""Shared data model: the contract between the engine (Person A) and the API (Person B).

Frozen in Phase 0. Changing a field here needs both people to agree (see Project.md).

A `Package` mirrors the shared trip format (data/DATA_DICTIONARY.md, section 4) so it can be stored
in package_versions.body and exported without a second shape. `to_trip_format()` / `from_trip_format()`
convert to and from that JSON.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Any, Literal

ItemType = Literal["flight", "hotel", "transfer", "attraction"]
ItemStatus = Literal["PLANNED", "BOOKED"]
Outcome = Literal["PACKAGE", "OVER_BUDGET", "NO_PACKAGE"]
OptionKind = Literal["hotel", "flight", "attraction"]
ChangeType = Literal["hotel", "flight", "add_attraction", "remove_attraction"]


# ---------------------------------------------------------------- request

@dataclass(frozen=True)
class TripRequest:
    departure_city: str              # e.g. "Bengaluru" (destinations.json departure_cities[].city)
    country: str                     # e.g. "Japan" (countries[].name)
    start_date: date                 # S: the arrival flight lands on this day
    nights: int                      # N
    adults: int
    children_ages: tuple[int, ...] = ()
    budget_inr: int = 0
    traveler_name: str = "Traveler"

    @property
    def children(self) -> int:
        return len(self.children_ages)

    @property
    def travelers(self) -> int:      # T
        return self.adults + self.children

    @property
    def end_date(self) -> date:      # L = S + N, the return day (no hotel night)
        return self.start_date + timedelta(days=self.nights)


# ---------------------------------------------------------------- package

@dataclass
class CityStay:
    city: str
    nights: int


@dataclass
class Item:
    """One line of the package, in trip format. Times are local: 'YYYY-MM-DDTHH:MM' or 'YYYY-MM-DD'."""
    item_id: str
    type: ItemType
    name: str
    city: str                        # flight: the arrival city
    catalog_id: str
    start: str
    end: str | None
    quantity: int                    # seats, rooms, vehicles or tickets
    price_inr: int
    room_id: str | None = None       # hotel items only
    status: ItemStatus = "PLANNED"
    booking: dict | None = None      # {"reference": "1234567890"} after confirm
    sources: list = field(default_factory=list)      # always [] in Problem 1
    warnings: list[str] = field(default_factory=list)


@dataclass
class Traveler:
    name: str
    home_airport: str
    adults: int
    children: int
    child_ages: list[int]


@dataclass
class Package:
    trip_id: str
    traveler: Traveler
    start_date: str                  # 'YYYY-MM-DD'
    end_date: str                    # return day
    country: str
    budget_inr: int
    city_plan: list[CityStay]
    items: list[Item]

    @property
    def total_inr(self) -> int:
        return sum(i.price_inr for i in self.items)

    def to_trip_format(self) -> dict[str, Any]:
        return {
            "trip_id": self.trip_id,
            "traveler": asdict(self.traveler),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "country": self.country,
            "budget_inr": self.budget_inr,
            "total_inr": self.total_inr,
            "city_plan": [asdict(c) for c in self.city_plan],   # extra field, allowed by the format
            "items": [asdict(i) for i in self.items],
        }

    @classmethod
    def from_trip_format(cls, d: dict[str, Any]) -> Package:
        return cls(
            trip_id=d["trip_id"],
            traveler=Traveler(**d["traveler"]),
            start_date=d["start_date"],
            end_date=d["end_date"],
            country=d["country"],
            budget_inr=d["budget_inr"],
            city_plan=[CityStay(**c) for c in d.get("city_plan", [])],
            items=[Item(**i) for i in d["items"]],
        )


@dataclass
class Totals:
    total_inr: int
    budget_inr: int
    by_type: dict[str, int]          # {"flight": ..., "hotel": ..., "transfer": ..., "attraction": ...}

    @property
    def left_inr(self) -> int:       # negative when over budget
        return self.budget_inr - self.total_inr

    @property
    def over_budget(self) -> bool:
        return self.total_inr > self.budget_inr


# ---------------------------------------------------------------- validator

@dataclass
class Violation:
    rule_id: str                     # e.g. "AT2"
    item_ref: str | None             # item_id, or None for package-level rules
    message: str                     # plain English, shown to the traveler


# ---------------------------------------------------------------- builder

@dataclass
class CityPlanSummary:
    plan: list[CityStay]
    total_inr: int | None            # None when the plan has no valid package
    valid: bool
    reason: str | None = None        # why it failed, when not valid


@dataclass
class BuildResult:
    outcome: Outcome
    package: Package | None = None                       # PACKAGE, or the cheapest one for OVER_BUDGET
    alternatives: dict[str, Package] = field(default_factory=dict)   # G4: cheapest / fastest / best_rated
    city_plans: list[CityPlanSummary] = field(default_factory=list)  # G3, ranked
    cheapest_total: int | None = None                    # OVER_BUDGET
    over_by: int | None = None                           # OVER_BUDGET
    suggestion: str | None = None                        # OVER_BUDGET (M8)
    reason: str | None = None                            # NO_PACKAGE (M2)


# ---------------------------------------------------------------- changes

@dataclass
class Option:
    kind: OptionKind
    catalog_id: str                  # hotel_id, flight_id or attraction_id
    label: str
    price_inr: int
    price_diff: int                  # G2: + more expensive, - cheaper than the current choice
    room_id: str | None = None       # hotel options
    start: str | None = None         # suggested start for attractions
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Change:
    type: ChangeType
    city: str | None = None          # hotel
    hotel_id: str | None = None      # hotel
    room_id: str | None = None       # hotel
    leg: Literal["arrival", "return"] | None = None   # flight
    flight_id: str | None = None     # flight
    date: str | None = None          # add_attraction
    attraction_id: str | None = None # add_attraction
    start: str | None = None         # add_attraction (optional)
    item_id: str | None = None       # remove_attraction


@dataclass
class ChangeResult:
    package: Package                 # NOT yet validated: the caller runs validate()
    side_effects: list[str] = field(default_factory=list)   # G1: "Airport transfer re-timed to 14:30"
    warnings: list[str] = field(default_factory=list)

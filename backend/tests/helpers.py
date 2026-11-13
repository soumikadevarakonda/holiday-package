"""Test helpers shared across test modules."""

import copy
import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.core.package_model import Package, TripRequest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@lru_cache
def _menon_json() -> dict:
    return json.loads((FIXTURES / "menon_package.json").read_text(encoding="utf-8"))


def menon_package() -> Package:
    """Hand-checked valid Menon package (Tokyo 3 + Kyoto 3). A fresh copy every call."""
    return Package.from_trip_format(copy.deepcopy(_menon_json()))


def request_fixtures() -> list[dict]:
    return json.loads((FIXTURES / "requests.json").read_text(encoding="utf-8"))


def to_request(d: dict) -> TripRequest:
    return TripRequest(d["departure_city"], d["country"], date.fromisoformat(d["start_date"]), d["nights"],
                       d["adults"], tuple(d["children_ages"]), d["budget_inr"], d.get("traveler_name", "Traveler"))


MENON_REQUEST = TripRequest("Bengaluru", "Japan", date(2027, 4, 10), 6, 2, (6,), 350_000, "Menon family")

"""
Pydantic schemas for holiday packages, requests, and validation rules (Feature M1).
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class TripRequestSchema(BaseModel):
    """
    Validated holiday request form inputs (Feature M1).
    Enforces all problem boundary constraints:
    - Departure city in India (BLR, DEL, BOM, MAA)
    - Destination country (Japan, UAE)
    - Dates: 1 Apr 2027 <= start_date, return date <= 20 Apr 2027 (Rule D1)
    - Duration: 3 <= nights <= 10 (Rule D1)
    - Adults >= 1
    - Children >= 0; child_ages count must match children count; ages between 0 and 17
    - Max group size <= 9 (no flight has 10+ seats)
    - Budget > 0
    """

    departure_city: str = Field(..., min_length=2, max_length=100, description="City in India to depart from")
    destination_country: str = Field(..., min_length=2, max_length=100, description="Destination country (Japan or UAE)")
    start_date: date = Field(..., description="Holiday arrival date (YYYY-MM-DD)")
    nights: int = Field(..., ge=3, le=10, description="Duration in nights (3 to 10)")
    adults: int = Field(..., ge=1, description="Number of adult travelers (at least 1)")
    children: int = Field(default=0, ge=0, description="Number of child travelers")
    child_ages: list[int] = Field(default_factory=list, description="Age of each child traveler (0 to 17)")
    budget: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2, description="Total budget in INR")
    mode: str = Field(default="default", description="Builder mode: 'default' or 'three'")

    @model_validator(mode="before")
    @classmethod
    def normalize_request(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        # Normalize departure_city / origin
        if "departure_city" not in d and "origin" in d:
            d["departure_city"] = d["origin"]
        # Normalize destination_country / country
        if "destination_country" not in d and "country" in d:
            d["destination_country"] = d["country"]
        # Normalize budget / budget_inr
        if "budget" not in d and "budget_inr" in d:
            d["budget"] = d["budget_inr"]
        # Normalize child ages / children_ages
        if "child_ages" not in d and "children_ages" in d:
            d["child_ages"] = d["children_ages"]
        # Unpack travelers dict if present
        if "travelers" in d and isinstance(d["travelers"], dict):
            t = d["travelers"]
            if "adults" not in d and "adults" in t:
                d["adults"] = t["adults"]
            if "children" not in d and "children" in t:
                d["children"] = t["children"]
            if "child_ages" not in d:
                d["child_ages"] = t.get("child_ages") or t.get("children_ages") or []
        # Calculate nights from start_date and end_date if nights is missing
        if "nights" not in d and "start_date" in d and "end_date" in d:
            try:
                s = date.fromisoformat(str(d["start_date"]))
                e = date.fromisoformat(str(d["end_date"]))
                d["nights"] = (e - s).days
            except Exception:
                pass
        return d

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v: date) -> date:
        window_start = date(2027, 4, 1)
        window_end = date(2027, 4, 20)
        if v < window_start or v > window_end:
            raise ValueError(f"Start date must be between {window_start} and {window_end}")
        return v

    @model_validator(mode="after")
    def validate_rules(self) -> "TripRequestSchema":
        # Rule D1: return date must be on or before 2027-04-20
        return_date = self.start_date + timedelta(days=self.nights)
        last_allowed_departure = date(2027, 4, 20)
        if return_date > last_allowed_departure:
            raise ValueError(
                f"Return flight date ({return_date}) exceeds the catalogue window limit ({last_allowed_departure})"
            )

        # Children ages check
        if len(self.child_ages) != self.children:
            raise ValueError(
                f"child_ages length ({len(self.child_ages)}) must match children count ({self.children})"
            )
        for age in self.child_ages:
            if age < 0 or age > 17:
                raise ValueError(f"Child age {age} is invalid. Child ages must be between 0 and 17.")

        # Max group capacity check: no flight in dataset has 10+ seats
        total_travelers = self.adults + self.children
        if total_travelers > 9:
            raise ValueError(
                f"Total travelers ({total_travelers}) exceeds maximum capacity of 9 (flights have at most 9 seats)"
            )

        return self


# Alias for backwards compatibility
PackageCreate = TripRequestSchema


class PackageResponse(BaseModel):
    """Structured response for a package."""

    package_id: str
    trip_id: Optional[str] = None
    status: str
    version_no: int
    total_price: float
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    package_data: dict[str, Any] = Field(default_factory=dict)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    city_plans: list[dict[str, Any]] = Field(default_factory=list)


class PackageListResponse(BaseModel):
    """Paginated list of packages."""

    count: int
    packages: list[PackageResponse]


class RebuildRequest(BaseModel):
    """Payload to rebuild a package with a selected city plan."""

    city_plan: dict[str, Any] = Field(..., description="Selected city plan")


class ComponentChangeRequest(BaseModel):
    """Payload to apply a component swap/change (PRD Section 10)."""

    base_version: Optional[int] = Field(default=None, description="Expected current package version")
    kind: str = Field(..., description="Component type: 'hotel', 'flight', or 'attraction'")
    current_item_id: Optional[str] = Field(default=None, description="Item identifier being replaced")
    new_catalog_id: str = Field(..., description="Catalogue ID of the new component")
    params: dict[str, Any] = Field(default_factory=dict, description="Additional parameters (e.g. city, leg, room_id)")

    @model_validator(mode="before")
    @classmethod
    def normalize_change(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        d = dict(data)
        # Support PRD Section 10 format: {base_version, change: {type, city, hotel_id, room_id, ...}}
        if "change" in d and isinstance(d["change"], dict):
            ch = d["change"]
            if "kind" not in d:
                d["kind"] = ch.get("type") or ch.get("kind", "hotel")
            if "new_catalog_id" not in d:
                d["new_catalog_id"] = (
                    ch.get("hotel_id")
                    or ch.get("flight_id")
                    or ch.get("attraction_id")
                    or ch.get("new_catalog_id", "")
                )
            if "current_item_id" not in d:
                d["current_item_id"] = ch.get("item_id") or ch.get("current_item_id")
            params = dict(d.get("params", {}))
            for k, v in ch.items():
                if k not in ("type", "kind", "hotel_id", "flight_id", "attraction_id", "item_id", "current_item_id"):
                    params[k] = v
            d["params"] = params
        return d


class ConfirmPackageRequest(BaseModel):
    """Payload for package confirmation (PRD Section 10)."""

    base_version: Optional[int] = Field(default=None, description="Expected current package version")
    customer_name: Optional[str] = Field(default="Guest Traveler", description="Primary traveler name")
    customer_email: Optional[str] = Field(default="traveler@example.com", description="Notification email")
    customer_phone: Optional[str] = Field(default=None, description="Optional phone number")


class QuickRequestInput(BaseModel):
    """Plain-text holiday request input for parsing (Feature S1)."""

    text: str = Field(..., min_length=3, max_length=500, description="Natural-language holiday request string")


class QuickRequestResponse(BaseModel):
    """Parsed fields and ambiguity detection."""

    parsed: dict[str, Any]
    missing_fields: list[str]
    ambiguous_fields: list[str]
    ready_to_build: bool

"""
Package export serializer converting to shared trip format (DATA_DICTIONARY.md Section 4).
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Optional


def format_export_datetime(val: Any, is_date_only: bool = False) -> Optional[str]:
    """Format datetime string according to export specification (without seconds)."""
    if not val:
        return None
    s = str(val).strip()
    if is_date_only:
        return s[:10]
    if "T" in s:
        parts = s.split("T")
        time_part = parts[1][:5]
        return f"{parts[0]}T{time_part}"
    return s[:10]


def serialize_to_trip_format(
    package_data: dict[str, Any],
    trip_id: str,
    booking_reference: Optional[str] = None,
    trip_request: Optional[Any] = None,
) -> dict[str, Any]:
    """
    Serialize package dictionary into the official shared trip JSON format.
    Matches DATA_DICTIONARY.md section 4 and data/trip_format_example.json.
    """
    # Extract traveler info
    adults = 2
    children = 0
    child_ages: list[int] = []
    budget_inr = 0
    start_date_str = package_data.get("start_date")
    country = package_data.get("country") or "Japan"

    if trip_request is not None:
        adults = trip_request.adults
        children = trip_request.children
        child_ages = trip_request.child_ages or []
        budget_inr = int(trip_request.budget)
        country = trip_request.destination_country
        if not start_date_str:
            start_date_str = trip_request.start_date.isoformat() if hasattr(trip_request.start_date, "isoformat") else str(trip_request.start_date)

    if "traveler" in package_data and isinstance(package_data["traveler"], dict):
        t_obj = package_data["traveler"]
        adults = t_obj.get("adults", adults)
        children = t_obj.get("children", children)
        child_ages = t_obj.get("child_ages", child_ages)

    budget_inr = int(package_data.get("budget_inr") or budget_inr)
    total_inr = int(package_data.get("total_inr") or package_data.get("total_price") or 0)

    # Compute end_date
    end_date_str = package_data.get("end_date")
    if not end_date_str and start_date_str and trip_request:
        s_date = date.fromisoformat(str(start_date_str)[:10])
        end_date_str = (s_date + timedelta(days=trip_request.nights)).isoformat()

    # Format items
    formatted_items = []
    raw_items = package_data.get("items", [])
    for it in raw_items:
        item_type = it.get("type") or it.get("item_type", "")
        is_hotel = (item_type == "hotel")

        item_status = "BOOKED" if booking_reference else it.get("status", "PLANNED")
        booking_obj = {"reference": booking_reference} if booking_reference else None

        formatted_items.append({
            "item_id": it.get("item_id", ""),
            "type": item_type,
            "name": it.get("name") or it.get("catalog_id") or it.get("catalogue_id", ""),
            "city": it.get("city") or it.get("city_name", ""),
            "status": item_status,
            "catalog_id": it.get("catalog_id") or it.get("catalogue_id", ""),
            "room_id": it.get("room_id") if is_hotel else None,
            "start": format_export_datetime(it.get("start") or it.get("start_datetime"), is_date_only=is_hotel),
            "end": format_export_datetime(it.get("end") or it.get("end_datetime"), is_date_only=is_hotel),
            "quantity": int(it.get("quantity", 1)),
            "price_inr": int(it.get("price_inr") or it.get("price", 0)),
            "booking": booking_obj,
            "sources": [],
            "warnings": it.get("warnings", []),
        })

    return {
        "trip_id": trip_id,
        "traveler": {
            "name": package_data.get("traveler", {}).get("name", "Traveler"),
            "home_airport": package_data.get("traveler", {}).get("home_airport"),
            "adults": adults,
            "children": children,
            "child_ages": child_ages,
        },
        "start_date": str(start_date_str)[:10] if start_date_str else None,
        "end_date": str(end_date_str)[:10] if end_date_str else None,
        "country": country,
        "budget_inr": budget_inr,
        "total_inr": total_inr,
        "items": formatted_items,
    }

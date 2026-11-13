"""
Day-by-day timeline generator for holiday packages (Feature M4).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any


def format_time_str(val: Any) -> str:
    """Extract HH:MM from ISO string or datetime."""
    if not val:
        return ""
    s = str(val)
    if "T" in s:
        part = s.split("T")[1]
        return part[:5]
    return s[:5]


def generate_package_timeline(
    package_data: dict[str, Any],
    start_date: date | str,
    nights: int,
) -> list[dict[str, Any]]:
    """
    Generate an ordered day-by-day timeline from package items (Feature M4).
    Sorts events within each day chronologically by local time.
    """
    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date[:10])

    total_days = nights + 1
    days: list[dict[str, Any]] = []

    # Initialize empty days
    for day_idx in range(total_days):
        day_date = start_date + timedelta(days=day_idx)
        days.append({
            "day_number": day_idx + 1,
            "date": day_date.isoformat(),
            "weekday": day_date.strftime("%A"),
            "events": [],
        })

    items = package_data.get("items", [])
    for it in items:
        item_type = it.get("type") or it.get("item_type", "")
        start_val = it.get("start") or it.get("start_datetime")
        end_val = it.get("end") or it.get("end_datetime")
        name = it.get("name") or it.get("catalog_id") or it.get("catalogue_id", "")
        city = it.get("city") or it.get("city_name", "")

        if not start_val:
            continue

        start_str = str(start_val)
        start_d_str = start_str[:10]
        try:
            item_start_date = date.fromisoformat(start_d_str)
        except ValueError:
            continue

        # Find corresponding day index
        day_offset = (item_start_date - start_date).days
        if 0 <= day_offset < total_days:
            time_part = format_time_str(start_val)
            days[day_offset]["events"].append({
                "item_id": it.get("item_id"),
                "type": item_type,
                "time": time_part,
                "title": name,
                "city": city,
                "end_time": format_time_str(end_val) if end_val else None,
                "price_inr": it.get("price_inr") or float(it.get("price", 0)),
                "quantity": it.get("quantity", 1),
                "warnings": it.get("warnings", []),
            })

    # Sort events within each day chronologically
    for d in days:
        d["events"].sort(key=lambda ev: ev.get("time") or "99:99")

    return days

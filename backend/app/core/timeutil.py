"""Time and date utilities: HH:MM and 24:00 parsing, past-midnight windows, weekday math.

Shared across rules, builder, and pricing.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def parse_hhmm(s: str) -> int:
    """Parse 'HH:MM' or '24:00' to minutes from midnight (0..1440)."""
    s = s.strip()
    if s == "24:00":
        return 1440
    parts = s.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {s}")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Time out of range: {s}")
    return h * 60 + m


def format_hhmm(minutes: int) -> str:
    """Format minutes from midnight (0..1440) as 'HH:MM' or '24:00'."""
    if minutes == 1440:
        return "24:00"
    m = minutes % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def time_in_window(t: str | int, window_from: str | int, window_until: str | int) -> bool:
    """Check if time t is inside [window_from, window_until] (both ends inclusive).

    Handles past-midnight wrap-around (e.g. 06:00 to 00:30).
    '24:00' is parsed as 1440 min (end of day).
    """
    t_min = parse_hhmm(t) if isinstance(t, str) else t
    f_min = parse_hhmm(window_from) if isinstance(window_from, str) else window_from
    u_min = parse_hhmm(window_until) if isinstance(window_until, str) else window_until

    # Normal window: e.g. 06:00 to 23:00, or 00:00 to 24:00
    if f_min <= u_min:
        return f_min <= t_min <= u_min

    # Window crosses midnight: e.g. 06:00 to 00:30 (360 to 30)
    # Valid times are either >= f_min (in the evening) or <= u_min (after midnight)
    return t_min >= f_min or t_min <= u_min


def weekday_of(d: date | str) -> str:
    """Return 3-letter uppercase weekday code: MON, TUE, WED, THU, FRI, SAT, SUN."""
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return WEEKDAYS[d.weekday()]


def parse_iso_datetime(s: str) -> datetime:
    """Parse ISO datetime string, supporting with or without seconds ('YYYY-MM-DDTHH:MM[:SS]')."""
    # Normalize 'T' or space separator
    s = s.replace(" ", "T")
    # Truncate optional seconds or timezone if present
    # Typical catalog: '2027-04-01T07:20:00'
    return datetime.fromisoformat(s)


def format_iso_hm(dt: datetime) -> str:
    """Format datetime as 'YYYY-MM-DDTHH:MM' (DATA_DICTIONARY shared trip format)."""
    return dt.strftime("%Y-%m-%dT%H:%M")


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """Add minutes to a datetime."""
    return dt + timedelta(minutes=minutes)


def minutes_between(start_dt: datetime, end_dt: datetime) -> int:
    """Return difference (end_dt - start_dt) in minutes.

    Note: Both must be in the same local time zone. Never subtract across timezones.
    """
    return int((end_dt - start_dt).total_seconds() // 60)


def next_grid_slot(service_from: str, frequency_minutes: int, earliest_time: str) -> str:
    """Find the earliest departure on the frequency grid at or after earliest_time.

    Example: service_from="06:00", frequency=30, earliest_time="10:00" -> "10:00".
    If earliest_time="09:40", slot is "10:00".
    """
    start_min = parse_hhmm(service_from)
    target_min = parse_hhmm(earliest_time)

    if target_min <= start_min:
        return format_hhmm(start_min)

    diff = target_min - start_min
    intervals = (diff + frequency_minutes - 1) // frequency_minutes
    slot_min = start_min + intervals * frequency_minutes
    return format_hhmm(slot_min)

"""Unit tests for app.core.timeutil."""

from datetime import date, datetime

import pytest
from app.core.timeutil import (
    add_minutes,
    format_hhmm,
    format_iso_hm,
    minutes_between,
    next_grid_slot,
    parse_hhmm,
    parse_iso_datetime,
    time_in_window,
    weekday_of,
)


def test_parse_and_format_hhmm():
    assert parse_hhmm("00:00") == 0
    assert parse_hhmm("06:30") == 390
    assert parse_hhmm("23:59") == 1439
    assert parse_hhmm("24:00") == 1440

    assert format_hhmm(0) == "00:00"
    assert format_hhmm(390) == "06:30"
    assert format_hhmm(1440) == "24:00"

    with pytest.raises(ValueError):
        parse_hhmm("25:00")
    with pytest.raises(ValueError):
        parse_hhmm("invalid")


def test_time_in_window_standard():
    # 06:00 to 23:00
    assert time_in_window("06:00", "06:00", "23:00") is True
    assert time_in_window("23:00", "06:00", "23:00") is True
    assert time_in_window("12:00", "06:00", "23:00") is True
    assert time_in_window("05:59", "06:00", "23:00") is False
    assert time_in_window("23:01", "06:00", "23:00") is False

    # 00:00 to 24:00 (24h)
    assert time_in_window("00:00", "00:00", "24:00") is True
    assert time_in_window("15:30", "00:00", "24:00") is True
    assert time_in_window("24:00", "00:00", "24:00") is True


def test_time_in_window_past_midnight():
    # KIX to Namba shuttle: 06:00 to 00:30 (crosses midnight)
    assert time_in_window("06:00", "06:00", "00:30") is True
    assert time_in_window("22:50", "06:00", "00:30") is True
    assert time_in_window("23:59", "06:00", "00:30") is True
    assert time_in_window("00:15", "06:00", "00:30") is True
    assert time_in_window("00:30", "06:00", "00:30") is True
    # Out of window (e.g. 01:00 or 05:00)
    assert time_in_window("00:31", "06:00", "00:30") is False
    assert time_in_window("03:00", "06:00", "00:30") is False
    assert time_in_window("05:59", "06:00", "00:30") is False


def test_weekday_of():
    # 10 April 2027 is a Saturday
    assert weekday_of("2027-04-10") == "SAT"
    # 11 April 2027 is a Sunday
    assert weekday_of(date(2027, 4, 11)) == "SUN"
    # 12 April 2027 is a Monday
    assert weekday_of("2027-04-12") == "MON"
    # 16 April 2027 is a Friday
    assert weekday_of("2027-04-16") == "FRI"


def test_iso_datetime_helpers():
    dt = parse_iso_datetime("2027-04-09T23:50:00")
    assert dt == datetime(2027, 4, 9, 23, 50, 0)
    assert format_iso_hm(dt) == "2027-04-09T23:50"

    dt_no_sec = parse_iso_datetime("2027-04-10T10:30")
    assert dt_no_sec == datetime(2027, 4, 10, 10, 30)

    later = add_minutes(dt_no_sec, 60)
    assert later == datetime(2027, 4, 10, 11, 30)
    assert minutes_between(dt_no_sec, later) == 60


def test_next_grid_slot():
    # Train 06:00 with frequency 30 min
    assert next_grid_slot("06:00", 30, "06:00") == "06:00"
    assert next_grid_slot("06:00", 30, "06:15") == "06:30"
    assert next_grid_slot("06:00", 30, "09:45") == "10:00"
    assert next_grid_slot("06:00", 30, "10:00") == "10:00"

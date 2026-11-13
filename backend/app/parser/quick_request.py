"""
Deterministic rule-based parser for natural-language holiday requests (Feature S1).
Extracts structured request fields using regular expressions without external AI calls.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

WORD_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

CITY_MAP = {
    "blr": "Bengaluru",
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "del": "Delhi",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "bom": "Mumbai",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "maa": "Chennai",
    "chennai": "Chennai",
    "madras": "Chennai",
}

COUNTRY_MAP = {
    "japan": "Japan",
    "jp": "Japan",
    "tokyo": "Japan",
    "kyoto": "Japan",
    "osaka": "Japan",
    "uae": "United Arab Emirates",
    "united arab emirates": "United Arab Emirates",
    "dubai": "United Arab Emirates",
    "abu dhabi": "United Arab Emirates",
}

MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5, "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

MONTH_REGEX_STR = "jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"


def _parse_date_string(s: str) -> date | None:
    """Parse common date formats in text."""
    s = s.strip().lower()
    # YYYY-MM-DD
    iso = re.search(r"\b(2027-\d{2}-\d{2})\b", s)
    if iso:
        try:
            return date.fromisoformat(iso.group(1))
        except ValueError:
            pass

    # "April 10, 2027" or "April 10 2027" or "April 10th"
    m_first = re.search(
        rf"\b({MONTH_REGEX_STR})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*,?\s*(2027))?\b",
        s,
    )
    if m_first:
        m_str = m_first.group(1)[:3]
        m_num = MONTH_MAP.get(m_str, 4)
        d_num = int(m_first.group(2))
        y_num = int(m_first.group(3)) if m_first.group(3) else 2027
        try:
            return date(y_num, m_num, d_num)
        except ValueError:
            pass

    # "10 April 2027" or "10th April"
    d_first = re.search(
        rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTH_REGEX_STR})(?:\s*,?\s*(2027))?\b",
        s,
    )
    if d_first:
        d_num = int(d_first.group(1))
        m_str = d_first.group(2)[:3]
        m_num = MONTH_MAP.get(m_str, 4)
        y_num = int(d_first.group(3)) if d_first.group(3) else 2027
        try:
            return date(y_num, m_num, d_num)
        except ValueError:
            pass

    return None


def parse_quick_request(text: str) -> dict[str, Any]:
    """
    Parse a plain-text holiday request into structured form fields:
    departure_city, destination_country, start_date, nights, adults, children, child_ages, budget.
    """
    parsed: dict[str, Any] = {}
    missing_fields: list[str] = []
    ambiguous_fields: list[str] = []

    lower_text = text.lower()

    # 1. Departure City
    dep_found: set[str] = set()
    for key, city in CITY_MAP.items():
        if re.search(r"\b" + re.escape(key) + r"\b", lower_text):
            dep_found.add(city)

    if len(dep_found) == 1:
        parsed["departure_city"] = list(dep_found)[0]
    elif len(dep_found) > 1:
        from_match = re.search(r"\bfrom\s+([a-zA-Z\s]+?)\b(?:\s+to|\s+on|\s+for|$)", lower_text)
        resolved = False
        if from_match:
            candidate = from_match.group(1).strip()
            if candidate in CITY_MAP:
                parsed["departure_city"] = CITY_MAP[candidate]
                resolved = True
        if not resolved:
            ambiguous_fields.append("departure_city")
            parsed["departure_city"] = list(dep_found)[0]
    else:
        missing_fields.append("departure_city")

    # 2. Destination Country
    dest_found: set[str] = set()
    for key, country in COUNTRY_MAP.items():
        if re.search(r"\b" + re.escape(key) + r"\b", lower_text):
            dest_found.add(country)

    if len(dest_found) == 1:
        parsed["destination_country"] = list(dest_found)[0]
    elif len(dest_found) > 1:
        ambiguous_fields.append("destination_country")
        parsed["destination_country"] = list(dest_found)[0]
    else:
        missing_fields.append("destination_country")

    # 3. Date & Nights parsing
    # Look for "from <date> to <date>" with month words or digits
    date_range_match = re.search(
        rf"\bfrom\s+((?:{MONTH_REGEX_STR}|\d{{1,2}})\s+[^,\.]*?)\s+to\s+((?:{MONTH_REGEX_STR}|\d{{1,2}})\s+[^,\.]*?)(?:\.|\s+budget|\s+moderate|\s+fast|$)",
        lower_text,
    )
    start_date: date | None = None
    end_date: date | None = None
    if date_range_match:
        start_date = _parse_date_string(date_range_match.group(1))
        end_date = _parse_date_string(date_range_match.group(2))

    if not start_date:
        start_date = _parse_date_string(lower_text)

    if start_date:
        parsed["start_date"] = start_date.isoformat()
    else:
        missing_fields.append("start_date")

    # Nights
    nights: int | None = None
    nights_match = re.search(r"\b(\d+)\s*(?:nights|night|n)\b", lower_text)
    if nights_match:
        nights = int(nights_match.group(1))
    elif start_date and end_date and end_date > start_date:
        nights = (end_date - start_date).days

    if nights is not None:
        parsed["nights"] = nights
        if end_date:
            parsed["end_date"] = end_date.isoformat()
    else:
        missing_fields.append("nights")

    # 4. Adults
    adults: int | None = None
    adults_match = re.search(r"\b(\d+|one|two|three|four|five)\s*(?:adults|adult|a|persons|person|people)\b", lower_text)
    if adults_match:
        val = adults_match.group(1)
        adults = int(val) if val.isdigit() else WORD_NUMBERS.get(val, 2)
    elif "family" in lower_text:
        adults = 2

    if adults is not None:
        parsed["adults"] = adults
    else:
        missing_fields.append("adults")

    # 5. Children & Ages
    child_count = 0
    child_ages: list[int] = []

    # Look for "one 10yo child", "1 child", "2 children", "one 10-year-old child"
    kids_match = re.search(
        r"\b(\d+|one|two|three|four)\s+(?:(\d+)\s*(?:yo|yr|year|years|year-old|years-old)\s+)?(?:children|child|kids|kid)\b",
        lower_text,
    )
    if kids_match:
        c_val = kids_match.group(1)
        child_count = int(c_val) if c_val.isdigit() else WORD_NUMBERS.get(c_val, 1)
        if kids_match.group(2):
            child_ages.append(int(kids_match.group(2)))
    else:
        # Generic "1 child", "2 kids"
        gen_kids = re.search(r"\b(\d+|one|two|three|four)\s*(?:children|child|kids|kid)\b", lower_text)
        if gen_kids:
            c_val = gen_kids.group(1)
            child_count = int(c_val) if c_val.isdigit() else WORD_NUMBERS.get(c_val, 1)

    # Search for additional ages
    age_matches = re.findall(r"\b(?:age[s]?|aged)\s*(\d+(?:\s*(?:,|and)\s*\d+)*)\b", lower_text)
    for match in age_matches:
        for num in re.findall(r"\d+", match):
            if int(num) not in child_ages:
                child_ages.append(int(num))

    # Also search for standalone "10yo" or "10 yo" or "10-year-old"
    if not child_ages:
        yo_match = re.findall(r"\b(\d+)\s*(?:yo|year-old|yr-old)\b", lower_text)
        for num in yo_match:
            child_ages.append(int(num))

    if child_count > 0 and len(child_ages) < child_count:
        while len(child_ages) < child_count:
            child_ages.append(6)

    parsed["children"] = child_count
    parsed["child_ages"] = child_ages

    # Map travelers sub-dict and pace/interests for convenience
    parsed["travelers"] = {
        "adults": parsed.get("adults", 0),
        "children": child_count,
        "child_ages": child_ages,
    }
    # Origin alias
    if "departure_city" in parsed:
        # map back to code e.g. Bengaluru -> BLR
        code_map = {"Bengaluru": "BLR", "Delhi": "DEL", "Mumbai": "BOM", "Chennai": "MAA"}
        parsed["origin"] = code_map.get(parsed["departure_city"], parsed["departure_city"])

    # 6. Budget
    budget: float | None = None
    # 1st priority: explicit currency symbol or "budget" prefix e.g. "budget ₹3,50,000", "₹3,50,000", "budget 3.5 lakh"
    explicit_budget = re.search(
        r"(?:budget\s*(?:of|is|:)?\s*)?(?:rs\.?|inr|₹)\s*(\d[\d,.]*)\b",
        lower_text,
    )
    if explicit_budget:
        val_str = explicit_budget.group(1).replace(",", "")
        try:
            budget = float(val_str)
        except ValueError:
            pass

    if budget is None:
        lakh_match = re.search(r"(?:budget\s*(?:of|is|:)?\s*)?(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs|l)\b", lower_text)
        if lakh_match:
            budget = float(lakh_match.group(1)) * 100000.0

    if budget is None:
        budget_word = re.search(r"budget\s*(?:of|is|:)?\s*(\d{4,9})\b", lower_text)
        if budget_word:
            budget = float(budget_word.group(1))

    if budget is not None:
        parsed["budget"] = budget
    else:
        missing_fields.append("budget")

    # 7. Pace
    if "moderate" in lower_text:
        parsed["pace"] = "moderate"
    elif "fast" in lower_text or "packed" in lower_text:
        parsed["pace"] = "fast"
    elif "relaxed" in lower_text or "slow" in lower_text:
        parsed["pace"] = "relaxed"

    ready_to_build = len(missing_fields) == 0 and len(ambiguous_fields) == 0

    return {
        "parsed": parsed,
        "missing_fields": missing_fields,
        "ambiguous_fields": ambiguous_fields,
        "ready_to_build": ready_to_build,
    }

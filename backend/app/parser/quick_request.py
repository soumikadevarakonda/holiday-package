"""S1: read a short request in plain words with rules only (regex + keywords, no AI) and fill the form.

Example: "2 adults 1 kid age 6 Bengaluru to Japan 10 Apr 6 nights 3.5 lakh"
-> departure_city Bengaluru, country Japan, start_date 2027-04-10, nights 6, adults 2, children_ages [6],
   budget_inr 350000.
Fields that are not found are left out; the form shows them empty. Words that were not understood are
returned in `unparsed`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from app.catalog.store import get_store

DEFAULT_YEAR = 2027   # the data window is April 2027

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
WORD_NUMBERS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                "eight": 8, "nine": 9, "ten": 10, "single": 1, "couple": 2}
CITY_ALIASES = {"bangalore": "Bengaluru", "bengaluru": "Bengaluru", "blr": "Bengaluru",
                "delhi": "Delhi", "new delhi": "Delhi", "del": "Delhi",
                "mumbai": "Mumbai", "bombay": "Mumbai", "bom": "Mumbai",
                "chennai": "Chennai", "madras": "Chennai", "maa": "Chennai"}
COUNTRY_ALIASES = {"japan": "Japan", "jp": "Japan", "tokyo": "Japan", "kyoto": "Japan", "osaka": "Japan",
                   "uae": "United Arab Emirates", "u.a.e": "United Arab Emirates", "u.a.e.": "United Arab Emirates",
                   "emirates": "United Arab Emirates", "united arab emirates": "United Arab Emirates",
                   "dubai": "United Arab Emirates", "abu dhabi": "United Arab Emirates"}
STOPWORDS = {"to", "from", "for", "and", "with", "in", "on", "of", "the", "a", "an", "trip", "holiday", "family",
             "we", "are", "i", "am", "us", "me", "my", "our", "want", "go", "going", "travel", "travelling",
             "traveling", "plan", "please", "budget", "starting", "start", "leaving", "around", "about", "total",
             "people", "persons", "pax", "under", "max", "maximum", "upto", "up", "inr", "rs", "rupees", "₹",
             "is", "be", "at", "by", "days", "day", "flying", "fly", "visit", "visiting", "year", "old", "years",
             "olds", "aged", "age", "ages", "kid", "kids", "child", "children"}

NUM = r"(\d+|" + "|".join(WORD_NUMBERS) + r")"


@dataclass
class ParseResult:
    request: dict = field(default_factory=dict)
    unparsed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _num(s: str) -> int:
    return int(s) if s.isdigit() else WORD_NUMBERS[s]


def _amount(value: str, unit: str | None) -> int:
    n = float(value.replace(",", ""))
    unit = (unit or "").lower()
    if unit in ("lakh", "lakhs", "lac", "lacs", "l"):
        n *= 100_000
    elif unit in ("crore", "crores", "cr"):
        n *= 10_000_000
    elif unit in ("k", "thousand"):
        n *= 1_000
    return round(n)


class _Text:
    """Lower-cased text with consumed spans blanked out, so the leftovers can be reported."""

    def __init__(self, text: str) -> None:
        self.original = text
        self.s = " " + text.lower().replace("’", "'") + " "

    def take(self, pattern: str) -> re.Match | None:
        m = re.search(pattern, self.s)
        if m:
            self.s = self.s[:m.start()] + " " * (m.end() - m.start()) + self.s[m.end():]
        return m

    def leftovers(self) -> list[str]:
        words = re.findall(r"[a-z0-9₹.'-]+", self.s)
        return [w for w in words if w.strip(".,-'") and w.strip(".,-'") not in STOPWORDS]


def parse_quick_request(text: str) -> ParseResult:
    t = _Text(text)
    req: dict = {}
    warn: list[str] = []

    # budget first, so its digits are not read as dates or counts
    m = (t.take(r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lacs?|l|crores?|cr|k|thousand)?\b")
         or t.take(r"\b([\d,]*\d(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr|k|thousand)\b")
         or t.take(r"budget\D{0,12}([\d,]{4,}(?:\.\d+)?)\b()"))
    if m:
        req["budget_inr"] = _amount(m.group(1), m.group(2))

    # dates: 2027-04-10 · 10/04/2027 · 10 Apr (2027) · April 10(th)
    mon = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
    if m := t.take(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    elif m := t.take(r"\b(\d{1,2})[/.](\d{1,2})(?:[/.](\d{2,4}))?\b"):
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3) or DEFAULT_YEAR)
    elif m := t.take(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?{mon}(?:\s+(\d{{4}}))?"):
        d, mo, y = int(m.group(1)), MONTHS[m.group(2)], int(m.group(3) or DEFAULT_YEAR)
    elif m := t.take(rf"\b{mon}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?"):
        mo, d, y = MONTHS[m.group(1)], int(m.group(2)), int(m.group(3) or DEFAULT_YEAR)
    else:
        m = None
    if m:
        y = y + 2000 if y < 100 else y
        try:
            req["start_date"] = date(y, mo, d).isoformat()
        except ValueError:
            warn.append(f"'{m.group(0).strip()}' is not a valid date.")

    # nights: "6 nights" · "a week" · "7 days" (= 6 nights)
    if m := t.take(rf"\b{NUM}\s*(?:-\s*)?nights?\b"):
        req["nights"] = _num(m.group(1))
    elif m := t.take(r"\b(?:a|one)\s+week\b"):
        req["nights"] = 7
    elif m := t.take(rf"\b{NUM}\s*(?:-\s*)?days?\b"):
        req["nights"] = _num(m.group(1)) - 1
        warn.append(f"Read {m.group(0).strip()} as {req['nights']} nights.")

    # adults / children
    if m := t.take(rf"\b{NUM}\s+(?:adults?|grown[- ]?ups?|parents?)\b"):
        req["adults"] = _num(m.group(1))
    elif t.take(r"\b(?:couple|me and my (?:wife|husband|partner)|my (?:wife|husband|partner) and i)\b"):
        req["adults"] = 2
    n_children = None
    if m := t.take(rf"\b{NUM}\s+(?:kids?|child(?:ren)?|sons?|daughters?)\b"):
        n_children = _num(m.group(1))
    ages: list[int] = []
    if m := t.take(r"\b(?:aged?|ages)\s+((?:\d{1,2}(?:\s*(?:,|and|&)\s*)?)+)"):
        ages = [int(x) for x in re.findall(r"\d{1,2}", m.group(1))]
    else:
        while m := t.take(r"\b(\d{1,2})\s*(?:-\s*)?(?:years?|yrs?|y)\s*(?:-\s*)?old\b"):
            ages.append(int(m.group(1)))
    if ages or n_children is not None:
        if n_children is not None and ages and len(ages) != n_children:
            warn.append(f"{n_children} child(ren) but {len(ages)} age(s) given; check the ages.")
        if n_children and not ages:
            warn.append(f"{n_children} child(ren) given without ages; please enter each child's age.")
        req["children_ages"] = ages
    elif "adults" in req:
        req["children_ages"] = []

    # places: departure city, then country (a destination city implies its country)
    store = get_store()
    deps = {dc.city for dc in store.indexes.departure_cities}
    for alias in sorted(CITY_ALIASES, key=len, reverse=True):
        if CITY_ALIASES[alias] in deps and t.take(rf"\b{re.escape(alias)}\b"):
            req["departure_city"] = CITY_ALIASES[alias]
            break
    for alias in sorted(COUNTRY_ALIASES, key=len, reverse=True):
        if t.take(rf"(?<![a-z]){re.escape(alias)}(?![a-z])"):
            req["country"] = COUNTRY_ALIASES[alias]
            break

    return ParseResult(request=req, unparsed=t.leftovers(), warnings=warn)

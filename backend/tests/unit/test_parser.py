"""S1: quick request parser (rules only)."""

import pytest

from app.parser.quick_request import parse_quick_request


@pytest.fixture(autouse=True)
def _catalog(catalog_store):
    return catalog_store


def test_brief_example():
    r = parse_quick_request("2 adults 1 kid age 6 Bengaluru to Japan 10 Apr 6 nights 3.5 lakh")
    assert r.request == {"departure_city": "Bengaluru", "country": "Japan", "start_date": "2027-04-10",
                         "nights": 6, "adults": 2, "children_ages": [6], "budget_inr": 350000}
    assert r.unparsed == [] and r.warnings == []


@pytest.mark.parametrize("text,expected", [
    ("from Bombay to Dubai April 5th a week budget Rs 2,50,000",
     {"departure_city": "Mumbai", "country": "United Arab Emirates", "start_date": "2027-04-05", "nights": 7,
      "budget_inr": 250000}),
    ("me and my wife from delhi to tokyo 2027-04-12 for 5 nights under 300k",
     {"departure_city": "Delhi", "country": "Japan", "start_date": "2027-04-12", "nights": 5, "adults": 2,
      "budget_inr": 300000}),
    ("Chennai to UAE 8/4 4 nights 3 adults 1 child 7 years old budget 400000",
     {"departure_city": "Chennai", "country": "United Arab Emirates", "start_date": "2027-04-08", "nights": 4,
      "adults": 3, "children_ages": [7], "budget_inr": 400000}),
    ("2 adults 2 kids aged 4 and 9 Bangalore to Abu Dhabi 3rd Apr 3 nights ₹1.2 lakh",
     {"departure_city": "Bengaluru", "country": "United Arab Emirates", "start_date": "2027-04-03", "nights": 3,
      "adults": 2, "children_ages": [4, 9], "budget_inr": 120000}),
])
def test_variants(text, expected):
    r = parse_quick_request(text)
    for k, v in expected.items():
        assert r.request.get(k) == v, k


def test_children_without_ages_warns():
    r = parse_quick_request("Japan trip 3 kids 10 apr")
    assert any("without ages" in w for w in r.warnings)


def test_unknown_words_are_reported():
    r = parse_quick_request("2 adults to Japan with a pet giraffe")
    assert "giraffe" in r.unparsed and r.request["country"] == "Japan"


def test_invalid_date_warns():
    r = parse_quick_request("Japan 31 Apr 4 nights")
    assert "start_date" not in r.request and r.warnings

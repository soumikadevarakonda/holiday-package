
import json
from functools import lru_cache
from pathlib import Path

CATALOG_DIR = Path(__file__).resolve().parents[3] / "data" / "catalog"


@lru_cache(maxsize=1)
def load_catalog():
    catalog = {}

    for file in CATALOG_DIR.glob("*.json"):
        with file.open("r", encoding="utf-8") as f:
            catalog[file.stem] = json.load(f)

    return catalog


def get_records(name):
    data = load_catalog().get(name)

    if data is None:
        raise ValueError(f"Catalogue '{name}' not found")

    if not isinstance(data, list):
        raise ValueError(f"'{name}' is not a list catalogue")

    return data


def get_summary():
    catalog = load_catalog()

    return {
        "catalogues": {
            name: len(data) if isinstance(data, list) else len(data)
            for name, data in catalog.items()
        },
        "total_records": sum(
            len(data) for data in catalog.values()
        ),
    }


def filter_records(name, city=None, origin=None, destination=None,
                   category=None, cabin=None, min_rating=None,
                   max_price=None):

    records = get_records(name)

    if city:
        records = [
            r for r in records
            if r.get("city", "").lower() == city.lower()
        ]

    if origin:
        records = [
            r for r in records
            if r.get("from", "").upper() == origin.upper()
        ]

    if destination:
        records = [
            r for r in records
            if r.get("to", "").upper() == destination.upper()
        ]

    if category:
        records = [
            r for r in records
            if r.get("category", "").upper() == category.upper()
        ]

    if cabin:
        records = [
            r for r in records
            if r.get("cabin", "").upper() == cabin.upper()
        ]

    if min_rating is not None:
        records = [
            r for r in records
            if r.get("rating", 0) >= min_rating
        ]

    if max_price is not None:
        records = [
            r for r in records
            if r.get("price_per_seat", r.get("price", {}))
             .get("amount", float("inf")) <= max_price
        ]

    return records

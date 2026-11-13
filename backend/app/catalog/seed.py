"""Copy data/catalog/*.json into the MySQL catalog tables (ER diagram in database/).

- This and catalog/loader.py are the only files that know raw JSON field names.
- The JSON files are never changed. The tables are re-filled only when the files' hash changes.
- Run by hand:  python -m app.catalog.seed          (skip if unchanged)
                python -m app.catalog.seed --force  (always re-fill)
"""

import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.config import get_settings
from app.core.database import get_engine

log = logging.getLogger(__name__)

CATALOG_FILES = ["destinations.json", "airports.json", "flights.json", "hotels.json",
                 "rooms.json", "availability.json", "transfers.json", "attractions.json"]

# Delete order (children first). Insert order is the reverse.
CATALOG_TABLES = ["link_transfer", "intercity_link", "airport_transfer", "city_transfer", "intercity_transfer",
                  "transfer", "room_availability", "room", "hotel", "attraction", "flight",
                  "city_airport", "departure_city", "airport", "destination_city", "country"]

AIRPORT_TYPES = {"AIRPORT_TAXI", "AIRPORT_BUS", "AIRPORT_VAN"}
CITY_TYPES = {"CITY_TAXI", "CITY_BUS"}
INTERCITY_TYPES = {"TRAIN", "INTERCITY_BUS", "INTERCITY_TAXI"}


def _amount(price: dict | None) -> int | None:
    return None if price is None else int(price["amount"])


def _dt(s: str) -> str:
    return s.replace("T", " ")


def _load(catalog_dir: Path) -> dict[str, Any]:
    return {f: json.loads((catalog_dir / f).read_text(encoding="utf-8")) for f in CATALOG_FILES}


def catalog_hash(catalog_dir: Path) -> str:
    h = hashlib.sha256()
    for f in CATALOG_FILES:
        h.update((catalog_dir / f).read_bytes())
    return h.hexdigest()


def _rows(data: dict[str, Any]) -> dict[str, list[dict]]:
    dest = data["destinations.json"]
    r: dict[str, list[dict]] = {t: [] for t in CATALOG_TABLES}

    for c in dest["countries"]:
        r["country"].append({"code": c["code"], "name": c["name"], "timezone": c["timezone"]})
        for city in c["cities"]:
            r["destination_city"].append({"country_code": c["code"], "name": city["name"]})
        for link in c["links"]:
            r["intercity_link"].append({"country_code": c["code"], "from_city": link["from_city"],
                                        "to_city": link["to_city"]})
            for tid in link["transfer_ids"]:
                r["link_transfer"].append({"country_code": c["code"], "from_city": link["from_city"],
                                           "to_city": link["to_city"], "transfer_id": tid})

    city_country = {row["name"]: row["country_code"] for row in r["destination_city"]}

    for a in data["airports.json"]:
        r["airport"].append({"code": a["code"], "name": a["name"], "city": a["city"], "country": a["country"],
                             "timezone": a["timezone"], "lat": a.get("lat"), "lng": a.get("lng")})
        for city in a.get("serves_cities") or []:      # missing field = serves no destination city
            r["city_airport"].append({"country_code": city_country[city], "city_name": city,
                                      "airport_code": a["code"]})

    for d in dest["departure_cities"]:
        r["departure_city"].append({"city": d["city"], "airport_code": d["airport"]})

    for f in data["flights.json"]:
        r["flight"].append({
            "flight_id": f["flight_id"], "airline": f["airline"], "flight_number": f["flight_number"],
            "from_airport": f["from"], "to_airport": f["to"],
            "departure_local": _dt(f["departure_local"]), "arrival_local": _dt(f["arrival_local"]),
            "stops": f["stops"], "duration_minutes": f["duration_minutes"],
            "price_per_seat": _amount(f["price_per_seat"]), "seats_left": f["seats_left"], "cabin": f["cabin"]})

    for h in data["hotels.json"]:
        r["hotel"].append({
            "hotel_id": h["hotel_id"], "name": h["name"], "aliases": json.dumps(h.get("aliases", [])),
            "city": h["city"], "area": h["area"], "lat": h.get("lat"), "lng": h.get("lng"),
            "stars": h["stars"], "rating": h["rating"], "check_in_from": h["check_in_from"],
            "check_out_until": h["check_out_until"], "family_friendly": h["family_friendly"],
            "image": h.get("image")})

    for rm in data["rooms.json"]:
        r["room"].append({
            "room_id": rm["room_id"], "hotel_id": rm["hotel_id"], "room_type": rm["room_type"], "name": rm["name"],
            "max_adults": rm["max_adults"], "max_children": rm["max_children"],
            "price_per_night": _amount(rm["price_per_night"]), "refundable": rm["refundable"]})

    for av in data["availability.json"]:
        r["room_availability"].append({"room_id": av["room_id"], "date": av["date"], "rooms_left": av["rooms_left"]})

    for t in data["transfers.json"]:
        r["transfer"].append({
            "transfer_id": t["transfer_id"], "type": t["type"], "name": t["name"],
            "from_point": t["from_point"], "to_point": t["to_point"], "max_passengers": t["max_passengers"],
            "service_from": t["service_from"], "service_until": t["service_until"],
            "duration_minutes": t["duration_minutes"], "pricing": t["pricing"],
            "price": _amount(t["price"]), "child_price": _amount(t.get("child_price"))})
        if t["type"] in AIRPORT_TYPES:
            r["airport_transfer"].append({"transfer_id": t["transfer_id"], "airport_code": t["airport"],
                                          "city": t["city"], "area": t.get("area")})
        elif t["type"] in CITY_TYPES:
            r["city_transfer"].append({"transfer_id": t["transfer_id"], "city": t["city"]})
        elif t["type"] in INTERCITY_TYPES:
            r["intercity_transfer"].append({
                "transfer_id": t["transfer_id"], "from_city": t["from_city"], "to_city": t["to_city"],
                "frequency_minutes": t.get("frequency_minutes"), "door_to_door": t.get("door_to_door")})
        else:
            raise ValueError(f"Unknown transfer type {t['type']} ({t['transfer_id']})")

    for a in data["attractions.json"]:
        r["attraction"].append({
            "attraction_id": a["attraction_id"], "name": a["name"], "name_ja": a.get("name_ja"),
            "city": a["city"], "category": a["category"], "lat": a.get("lat"), "lng": a.get("lng"),
            "open_days": json.dumps(a["open_days"]), "open_from": a["open_from"], "open_until": a["open_until"],
            "closed_dates": json.dumps(a.get("closed_dates", [])), "aliases": json.dumps(a.get("aliases", [])),
            "visit_minutes": a["visit_minutes"], "child_friendly": a["child_friendly"],
            "accessible": a["accessible"], "price_per_person": _amount(a["price_per_person"]),
            "child_price": _amount(a.get("child_price")), "image": a.get("image")})
    return r


def _insert(conn: Connection, table: str, rows: list[dict]) -> None:
    if not rows:
        return
    cols = list(rows[0].keys())
    # Backticks: some column names are MySQL reserved words (e.g. `accessible`).
    sql = f"INSERT INTO `{table}` ({', '.join(f'`{c}`' for c in cols)}) VALUES ({', '.join(':' + c for c in cols)})"
    conn.execute(text(sql), rows)


def seeded_hash(conn: Connection) -> str | None:
    row = conn.execute(text("SELECT meta_value FROM catalog_meta WHERE meta_key = 'source_hash'")).first()
    return json.loads(row[0]) if row else None


def seed_catalog(force: bool = False) -> dict[str, int] | None:
    """Fill the catalog tables. Returns row counts, or None when the tables were already current."""
    catalog_dir = get_settings().catalog_dir
    digest = catalog_hash(catalog_dir)
    with get_engine().begin() as conn:
        if not force and seeded_hash(conn) == digest:
            log.info("Catalog tables already current (hash %s…)", digest[:12])
            return None
        rows = _rows(_load(catalog_dir))
        for table in CATALOG_TABLES:
            conn.execute(text(f"DELETE FROM {table}"))
        for table in reversed(CATALOG_TABLES):
            _insert(conn, table, rows[table])
        rules = _load(catalog_dir)["destinations.json"]["rules"]
        for key, value in (("rules", rules), ("source_hash", digest)):
            conn.execute(text("REPLACE INTO catalog_meta (meta_key, meta_value) VALUES (:k, :v)"),
                         {"k": key, "v": json.dumps(value)})
    counts = {t: len(rows[t]) for t in reversed(CATALOG_TABLES)}
    log.info("Catalog seeded: %s", counts)
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = seed_catalog(force="--force" in sys.argv)
    print("Already current, nothing to do." if result is None else json.dumps(result, indent=2))

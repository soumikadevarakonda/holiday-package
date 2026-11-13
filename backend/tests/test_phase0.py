"""Phase 0 exit checks: the app starts, shared plumbing works, the engine keeps its frozen interface."""

import json
from datetime import date
from pathlib import Path

from app.builder.search import build, rebuild
from app.catalog.seed import _load, _rows
from app.changes.options import options
from app.changes.side_effects import apply_change
from app.core.config import get_settings
from app.core.package_model import Change, Package, TripRequest
from app.rules.validator import validate

MENON = TripRequest("Bengaluru", "Japan", date(2027, 4, 10), 6, 2, (6,), 350_000, "Menon family")


def test_health_answers_without_db(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert set(r.json()) >= {"status", "db", "catalog_seeded", "catalog_loaded"}


def test_docs_and_openapi(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").json()["info"]["title"] == "Build My Holiday API"


def test_images_and_credits_are_served(client):
    assert client.get("/images/attractions/ATT-KYO-001.jpg").status_code == 200
    assert "Image credits" in client.get("/images/ATTRIBUTIONS.md").text


def test_unknown_route_uses_error_shape(client):
    body = client.get("/api/nope").json()
    assert set(body) == {"code", "message", "details"} and body["code"] == "NOT_FOUND"


def test_menon_fixture_round_trips_trip_format(menon):
    d = menon.to_trip_format()
    assert Package.from_trip_format(d).to_trip_format() == d
    assert d["total_inr"] == sum(i["price_inr"] for i in d["items"])
    example = json.loads((get_settings().DATA_DIR / "trip_format_example.json").read_text(encoding="utf-8"))
    assert set(example["items"][0]) <= set(d["items"][0])        # every example item field is present


def test_engine_functions_keep_their_frozen_signatures(menon):
    result = build(MENON, mode="three")
    assert result.outcome == "PACKAGE" and set(result.alternatives) == {"cheapest", "fastest", "best_rated"}
    assert rebuild(MENON, result.package.city_plan).package is not None
    assert validate(menon) == []
    current = [o for o in options(menon, "hotel", city="Tokyo") if o.details["current"]]
    assert len(current) == 1 and current[0].price_diff == 0
    att = next(i for i in menon.items if i.type == "attraction")
    after = apply_change(menon, Change(type="remove_attraction", item_id=att.item_id)).package
    assert len(after.items) == len(menon.items) - 1 and len(menon.items) == 11   # original untouched


def test_catalog_maps_onto_er_tables():
    rows = _rows(_load(get_settings().catalog_dir))
    assert len(rows["flight"]) == 469 and len(rows["room_availability"]) == 2500
    assert len(rows["transfer"]) == 66 == (len(rows["airport_transfer"]) + len(rows["city_transfer"])
                                           + len(rows["intercity_transfer"]))
    assert {(r["city_name"], r["airport_code"]) for r in rows["city_airport"]} >= {("Kyoto", "KIX"), ("Osaka", "KIX")}
    assert not any(r["airport_code"] == "ITM" for r in rows["city_airport"])
    # child_price 0 must survive as 0, not become NULL
    assert any(r["child_price"] == 0 for r in rows["attraction"])


def test_schema_files_are_ordered():
    names = sorted(p.name for p in get_settings().schema_dir.glob("*.sql"))
    assert names[0].startswith("001_catalog") and names[-1] == "011_inventory_usage.sql"
    assert Path(get_settings().DATABASE_DIR / "init" / "000_create_database.sql").is_file()

"""Endpoints 1-2: GET /api/health, GET /api/meta (and / -> /docs)."""


def test_health_reports_db_and_catalog(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert set(r.json()) >= {"status", "db", "catalog_seeded", "catalog_loaded", "catalog_source"}
    assert r.json()["catalog_loaded"] is True


def test_root_redirects_to_docs(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/docs"


def test_meta_endpoint(client):
    r = client.get("/api/meta")
    assert r.status_code == 200
    data = r.json()
    cities = {d["city"]: d["airport"] for d in data["departure_cities"]}
    assert cities == {"Bengaluru": "BLR", "Delhi": "DEL", "Mumbai": "BOM", "Chennai": "MAA"}
    countries = {c["name"]: c for c in data["countries"]}
    assert set(countries["Japan"]["cities"]) == {"Tokyo", "Kyoto", "Osaka"}
    assert set(countries["United Arab Emirates"]["cities"]) == {"Dubai", "Abu Dhabi"}
    rules = data["rules"]
    assert (rules["min_nights"], rules["max_nights"], rules["min_nights_per_city"]) == (3, 10, 2)
    assert rules["data_window"] == {"first_night": "2027-04-01", "last_departure": "2027-04-20"}
    assert data["max_flight_seats"] == 9

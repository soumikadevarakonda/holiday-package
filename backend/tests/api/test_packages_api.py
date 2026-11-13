"""API tests for catalog metadata and packages (Milestone M-1)."""


def test_meta_endpoint(client):
    r = client.get("/api/meta")
    assert r.status_code == 200
    data = r.json()

    # Departure cities
    assert len(data["departure_cities"]) == 4
    cities = {d["city"]: d["airport"] for d in data["departure_cities"]}
    assert cities["Bengaluru"] == "BLR"
    assert cities["Delhi"] == "DEL"
    assert cities["Mumbai"] == "BOM"
    assert cities["Chennai"] == "MAA"

    # Destination countries
    countries = {c["name"]: c for c in data["countries"]}
    assert "Japan" in countries
    assert "United Arab Emirates" in countries
    assert set(countries["Japan"]["cities"]) == {"Tokyo", "Kyoto", "Osaka"}
    assert set(countries["United Arab Emirates"]["cities"]) == {"Dubai", "Abu Dhabi"}

    # Rules metadata
    rules = data["rules"]
    assert rules["min_nights"] == 3
    assert rules["max_nights"] == 10
    assert rules["min_nights_per_city"] == 2
    assert rules["data_window"]["first_night"] == "2027-04-01"
    assert rules["data_window"]["last_departure"] == "2027-04-20"

    # Dynamic seat capacity from catalog
    assert data["max_flight_seats"] == 9


def test_parse_endpoint(client):
    r = client.post("/api/parse", json={"text": "2 adults 1 kid age 6 Bengaluru to Japan 10 Apr 6 nights 3.5 lakh"})
    assert r.status_code == 200
    assert r.json()["request"]["budget_inr"] == 350000


def test_parse_endpoint_rejects_empty_text(client):
    r = client.post("/api/parse", json={"text": ""})
    assert r.status_code == 422 and r.json()["code"] == "INVALID_INPUT"

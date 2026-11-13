"""Endpoint 3: POST /api/parse (S1, rules only)."""


def test_parse_brief_example(client):
    r = client.post("/api/parse", json={"text": "2 adults 1 kid age 6 Bengaluru to Japan 10 Apr 6 nights 3.5 lakh"})
    assert r.status_code == 200
    assert r.json()["request"] == {"departure_city": "Bengaluru", "country": "Japan", "start_date": "2027-04-10",
                                   "nights": 6, "adults": 2, "children_ages": [6], "budget_inr": 350000}


def test_parse_result_can_be_built_directly(client):
    parsed = client.post("/api/parse", json={"text": "me and my wife from Mumbai to Dubai 5 Apr 5 nights 2 lakh"})
    r = client.post("/api/packages", json=parsed.json()["request"])
    assert r.status_code == 201 and r.json()["outcome"] == "PACKAGE"


def test_parse_reports_unknown_words(client):
    r = client.post("/api/parse", json={"text": "2 adults to Japan with a pet giraffe"})
    assert "giraffe" in r.json()["unparsed"]


def test_parse_rejects_empty_text(client):
    r = client.post("/api/parse", json={"text": ""})
    assert r.status_code == 422 and r.json()["code"] == "INVALID_INPUT"

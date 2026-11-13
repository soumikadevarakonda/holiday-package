"""
API tests for Quick Request Natural Language Parser (Endpoint 3: POST /api/parse).
"""

from fastapi.testclient import TestClient


def test_parse_menon_family_request(client: TestClient):
    """
    Test parsing the exact Menon family prompt:
    "We are a family of 3 (2 adults, one 10yo child) from Bangalore wanting to visit Japan
     from April 10 2027 to April 16 2027. Budget ₹3,50,000. Moderate pace."
    """
    payload = {
        "text": (
            "We are a family of 3 (2 adults, one 10yo child) from Bangalore wanting to visit Japan "
            "from April 10 2027 to April 16 2027. Budget ₹3,50,000. Moderate pace."
        )
    }
    response = client.post("/api/parse", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["parsed"]["origin"] == "BLR"
    assert data["parsed"]["destination_country"] == "Japan"
    assert data["parsed"]["start_date"] == "2027-04-10"
    assert data["parsed"]["end_date"] == "2027-04-16"
    assert data["parsed"]["travelers"]["adults"] == 2
    assert data["parsed"]["travelers"]["children"] == 1
    assert data["parsed"]["travelers"]["child_ages"] == [10]
    assert data["parsed"]["budget"] == 350000
    assert data["parsed"]["pace"] == "moderate"
    assert data["missing_fields"] == []


def test_parse_partial_request(client: TestClient):
    """Test partial natural language request detecting missing fields."""
    payload = {
        "text": "Trip to Japan from Delhi for 2 adults in May"
    }
    response = client.post("/api/parse", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["parsed"]["destination_country"] == "Japan"
    assert data["parsed"]["origin"] == "DEL"
    assert data["parsed"]["travelers"]["adults"] == 2
    # Dates or budget may be missing
    assert "budget" in data["missing_fields"] or "start_date" in data["missing_fields"]


def test_parse_empty_text_validation_error(client: TestClient):
    """Test empty string fails validation."""
    response = client.post("/api/parse", json={"text": ""})
    assert response.status_code == 422

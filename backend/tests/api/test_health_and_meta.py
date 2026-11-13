"""
API tests for Health and Meta endpoints (Endpoints 1 and 2).
"""

from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """GET /api/health should return status and component health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "ok")
    assert "dependencies" in data or "components" in data


def test_meta_endpoint(client: TestClient):
    """GET /api/meta should return travel catalogue constraints and supported parameters."""
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json()
    assert "destination_countries" in data or "destinations" in data
    assert "departure_cities" in data
    assert "rules" in data

    # Verify Tokyo/Japan exists in destinations
    destinations = data.get("destination_countries") or data.get("destinations")
    assert any("Japan" in str(d) for d in destinations)

    # Verify Bangalore exists in departure cities
    departure_cities = data["departure_cities"]
    assert any("BLR" in str(c) or "Bengaluru" in str(c) or "Bangalore" in str(c) for c in departure_cities)

"""
API tests for Export Endpoint (Endpoint 13: GET /api/packages/{package_id}/export).
Verifies conformance with DATA_DICTIONARY.md Section 4 (Trip Format Specification).
"""

from fastapi.testclient import TestClient

MENON_REQUEST_PAYLOAD = {
    "origin": "BLR",
    "destination_country": "Japan",
    "start_date": "2027-04-10",
    "end_date": "2027-04-16",
    "travelers": {
        "adults": 2,
        "children": 1,
        "child_ages": [10],
    },
    "budget": 350000,
    "pace": "moderate",
    "interests": ["culture", "sightseeing"],
}


def test_export_package_format_and_headers(client: TestClient, mock_engine):
    """GET /api/packages/{package_id}/export produces official trip format with attachment header."""
    create_res = client.post("/api/packages", json=MENON_REQUEST_PAYLOAD)
    pkg_id = create_res.json()["package_id"]

    export_res = client.get(f"/api/packages/{pkg_id}/export")
    assert export_res.status_code == 200

    # Header checks
    assert export_res.headers["content-type"].startswith("application/json")
    content_disp = export_res.headers.get("content-disposition", "")
    assert "attachment" in content_disp
    assert f"trip-{pkg_id}.json" in content_disp or f"{pkg_id}.json" in content_disp

    # Structure checks per DATA_DICTIONARY.md Section 4
    data = export_res.json()
    assert "trip_id" in data
    assert "traveler" in data
    assert "country" in data
    assert "start_date" in data
    assert "end_date" in data
    assert "budget_inr" in data
    assert "total_inr" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0


def test_export_nonexistent_package_returns_404(client: TestClient):
    """GET /api/packages/{package_id}/export for unknown package returns 404."""
    res = client.get("/api/packages/non-existent-pkg-000/export")
    assert res.status_code == 404

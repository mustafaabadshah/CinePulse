"""Integration tests for NLPService lifecycle, API endpoints, and search enhancement."""

import pytest
from app.services.nlp.service import NLPService


def test_nlp_service_uninitialized_fallback():
    service = NLPService()
    assert service.is_ready is False
    res = service.parse_query("Ehd E Wafa Episode 3")
    assert res.is_nlp_assisted is False
    assert res.remaining_query == "Ehd E Wafa Episode 3"
    assert res.diagnostics.get("status") == "nlp_not_initialized"


def test_nlp_status_endpoint(client):
    response = client.get("/api/nlp/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_available" in data
    assert "patterns_loaded" in data
    assert "device" in data
    assert data["device"] == "cpu"


def test_nlp_parse_endpoint(client):
    response = client.post("/api/nlp/parse", json={"q": "Ehd E Wafa Episode 3"})
    assert response.status_code == 200
    data = response.json()
    assert data["original_query"] == "Ehd E Wafa Episode 3"
    assert data["is_nlp_assisted"] is True
    assert data["episode_number"] == 3
    assert len(data["recognized_entities"]) >= 1


def test_nlp_search_integration(client):
    response = client.get("/api/search?q=Ehd%20E%20Wafa%20Episode%203")
    assert response.status_code == 200
    data = response.json()
    assert "nlp" in data
    assert data["nlp"] is not None
    assert data["nlp"]["is_nlp_assisted"] is True
    assert data["nlp"]["episode_number"] == 3
    # Result should include episode hits
    assert len(data["hits"]) >= 1
    top_hit = data["hits"][0]
    assert "Ehd E Wafa" in (top_hit.get("program_name") or top_hit.get("title"))

"""Tests for Meilisearch query execution and filter allowlisting."""


def test_search_endpoint_empty_query(client):
    response = client.get("/api/search")
    assert response.status_code == 200
    data = response.json()
    assert "hits" in data
    assert "total_hits" in data
    assert "facet_distribution" in data
    assert "processing_time_ms" in data


def test_search_endpoint_with_query_and_type(client):
    response = client.get("/api/search?q=machine&type=researchers")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "researchers"
    assert isinstance(data["hits"], list)


def test_search_endpoint_with_filter(client):
    response = client.get("/api/search?type=researchers&country=United%20States")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "researchers"

"""Tests for Meilisearch query execution and filter allowlisting on Tamasha media catalog."""


def test_search_endpoint_empty_query(client):
    response = client.get("/api/search")
    assert response.status_code == 200
    data = response.json()
    assert "hits" in data
    assert "total_hits" in data
    assert "facet_distribution" in data
    assert "processing_time_ms" in data


def test_search_endpoint_with_query_and_media_type(client):
    response = client.get("/api/search?q=tamasha&type=episodes")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "episodes"
    assert isinstance(data["hits"], list)

    response_p = client.get("/api/search?q=tamasha&type=programs")
    assert response_p.status_code == 200
    data_p = response_p.json()
    assert data_p["type"] == "programs"
    assert isinstance(data_p["hits"], list)


def test_search_endpoint_with_media_filters(client):
    response = client.get("/api/search?type=episodes&is_free=true")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "episodes"
    assert isinstance(data["hits"], list)

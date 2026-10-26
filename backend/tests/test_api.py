"""API integration tests for public entity retrieval and health checks."""

from app.models import Episode, Program


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "components" in data
    assert "database" in data["components"]
    assert "meilisearch" in data["components"]


def test_media_catalog_endpoints(client, db_session):
    # Seed a program and episode
    prog = Program(
        id="prog_health_test",
        name="Trending News Bulletin",
        slug="trending-news-bulletin",
        channel_name="Express News",
        info_language="Urdu",
        info_genre="News",
    )
    db_session.add(prog)
    db_session.commit()

    ep = Episode(
        id="ep_health_test",
        title="Breaking News Headlines",
        slug="breaking-news-headlines",
        program_id="prog_health_test",
        views=12000,
        is_free=True,
    )
    db_session.add(ep)
    db_session.commit()

    # List programs
    res_p = client.get("/api/programs")
    assert res_p.status_code == 200
    p_data = res_p.json()
    assert any(item["id"] == "prog_health_test" for item in p_data["items"])

    # List episodes
    res_e = client.get("/api/episodes")
    assert res_e.status_code == 200
    e_data = res_e.json()
    assert any(item["id"] == "ep_health_test" for item in e_data["items"])

"""API integration tests for public entity retrieval and health checks."""

from app.models import Institution, Publication, Researcher


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "components" in data
    assert "database" in data["components"]
    assert "meilisearch" in data["components"]


def test_researchers_endpoints(client, db_session):
    # Seed an institution and researcher
    inst = Institution(
        id="inst_test",
        name="Test Institute of Tech",
        normalized_name="test institute of tech",
        country="United States",
        city="Boston",
    )
    db_session.add(inst)
    db_session.commit()

    res = Researcher(
        id="res_test_user",
        full_name="Dr. Test User",
        institution_id="inst_test",
        country="United States",
        department="Computer Science",
        research_interests=["ML", "Vision"],
        is_synthetic=True,
    )
    db_session.add(res)
    db_session.commit()

    # List
    response = client.get("/api/researchers")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert items[0]["id"] == "res_test_user"

    # Single
    single_res = client.get("/api/researchers/res_test_user")
    assert single_res.status_code == 200
    data = single_res.json()
    assert data["researcher"]["full_name"] == "Dr. Test User"
    assert data["institution"]["name"] == "Test Institute of Tech"


def test_publications_endpoints(client, db_session):
    pub = Publication(
        id="pub_test_paper",
        title="Scalable Machine Learning at Scale",
        authors=["Dr. Test User"],
        publication_year=2025,
        venue="NeurIPS 2025",
        keywords=["ML", "Scale"],
        is_synthetic=True,
    )
    db_session.add(pub)
    db_session.commit()

    response = client.get("/api/publications")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert items[0]["id"] == "pub_test_paper"

    single_pub = client.get("/api/publications/pub_test_paper")
    assert single_pub.status_code == 200
    assert single_pub.json()["publication"]["title"] == "Scalable Machine Learning at Scale"

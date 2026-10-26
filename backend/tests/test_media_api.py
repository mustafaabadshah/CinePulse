"""API integration tests for episodes, programs, and administrative endpoints."""

import pytest
from app.models.program import Program
from app.models.episode import Episode


def test_episodes_api(client, db_session):
    # Seed program and episode
    prog = Program(
        id="prog_api_test",
        name="Test Media Show",
        slug="test-media-show",
        channel_name="Geo News",
        info_language="Urdu",
        info_content_type="Talk Show",
    )
    db_session.add(prog)
    db_session.commit()

    ep = Episode(
        id="ep_api_test",
        title="Test Episode 101",
        slug="test-episode-101",
        program_id="prog_api_test",
        views=5000,
        is_free=True,
    )
    db_session.add(ep)
    db_session.commit()

    # List episodes
    res = client.get("/api/episodes?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert any(item["id"] == "ep_api_test" for item in data["items"])

    # Single episode
    res_single = client.get("/api/episodes/ep_api_test")
    assert res_single.status_code == 200
    ep_data = res_single.json()
    assert ep_data["id"] == "ep_api_test"
    assert ep_data["title"] == "Test Episode 101"
    assert ep_data["program"]["name"] == "Test Media Show"


def test_programs_api(client, db_session):
    prog = Program(
        id="prog_api_test_2",
        name="Automotive Review Series",
        slug="automotive-review-series",
        channel_name="PakWheels",
        info_language="Urdu",
    )
    db_session.add(prog)
    db_session.commit()

    ep = Episode(
        id="ep_api_test_2",
        title="Review of Electric Sedan",
        slug="review-of-electric-sedan",
        program_id="prog_api_test_2",
        views=25000,
        is_free=True,
    )
    db_session.add(ep)
    db_session.commit()

    # List programs
    res = client.get("/api/programs?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert any(item["id"] == "prog_api_test_2" for item in data["items"])

    # Single program
    res_single = client.get("/api/programs/prog_api_test_2")
    assert res_single.status_code == 200
    p_data = res_single.json()
    assert p_data["id"] == "prog_api_test_2"
    assert len(p_data["episodes"]) >= 1


def test_admin_source_files_and_status(client, admin_headers):
    # Test source files endpoint
    res = client.get("/api/admin/source-files", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "files" in data
    assert "enrichment_file" in data["files"]
    assert "episodes_file" in data["files"]
    assert data["files"]["enrichment_file"]["exists"] is True
    assert data["files"]["episodes_file"]["exists"] is True

    # Test index status endpoint
    res_status = client.get("/api/admin/index-status", headers=admin_headers)
    assert res_status.status_code == 200
    s_data = res_status.json()
    assert "indexes" in s_data
    assert "episodes" in s_data["indexes"]
    assert "programs" in s_data["indexes"]


def test_admin_import_dry_run_endpoint(client, admin_headers):
    # Trigger dry-run import
    res = client.post("/api/admin/import?dry_run=true", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["dry_run"] is True
    assert data["status"] in ("completed", "dry_run_completed")
    assert data["records_processed"] >= 7181

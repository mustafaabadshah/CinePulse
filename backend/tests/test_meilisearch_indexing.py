"""Tests for Meilisearch indexer service and media search."""

import pytest
from app.services.meilisearch_indexer import MeilisearchIndexer
from app.search.indexes import INDEX_EPISODES, INDEX_PROGRAMS, ALL_INDEXES
from app.models.program import Program
from app.models.episode import Episode


def test_index_definitions_and_settings():
    assert INDEX_EPISODES == "episodes"
    assert INDEX_PROGRAMS == "programs"
    assert INDEX_EPISODES in ALL_INDEXES
    assert INDEX_PROGRAMS in ALL_INDEXES


def test_meilisearch_indexer_setup_and_status(db_session):
    indexer = MeilisearchIndexer(db_session)
    # Ensure indexes exist and verify status
    res = indexer.setup_indexes()
    assert res.get("status") in ("ready", "configured")

    status = indexer.get_index_status()
    assert "indexes" in status
    assert "episodes" in status["indexes"]
    assert "programs" in status["indexes"]
    assert "healthy" in status
    assert status["healthy"] is True


def test_meilisearch_indexer_document_preparation(db_session):
    indexer = MeilisearchIndexer(db_session)

    # Add a mock program and episode with valid columns
    prog = Program(
        id="test_prog_999",
        name="Test Drama Serial",
        slug="test-drama-serial",
        channel_name="ARY Digital",
        info_language="Urdu",
        info_genre="Dramas",
        info_staring="Actor A, Actor B",
    )
    db_session.add(prog)
    db_session.commit()

    ep = Episode(
        id="test_ep_888",
        title="Test Drama Episode 1",
        slug="test-drama-episode-1",
        description="The opening episode of the drama.",
        program_id="test_prog_999",
        episode_number=1,
        views=150000,
        is_free=True,
        is_enable=True,
        genre="Dramas",
    )
    db_session.add(ep)
    db_session.commit()

    # Index both entities
    prog_result = indexer.index_programs(batch_size=10)
    assert prog_result.get("documents_indexed", 0) >= 1

    ep_result = indexer.index_episodes(batch_size=10)
    assert ep_result.get("documents_indexed", 0) >= 1

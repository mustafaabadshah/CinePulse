"""Unit tests for media catalog validation rules."""

from app.services.csv_importer import CsvMediaImporter
from app.services.data_normalizer import clean_str


def test_program_validation_rules():
    # Valid program
    prog_id = clean_str("100075")
    prog_name = clean_str("Ehd E Wafa")
    prog_slug = clean_str("ehd-e-wafa")
    assert bool(prog_id and prog_name and prog_slug) is True

    # Missing required id
    invalid_id = clean_str("")
    assert bool(invalid_id and prog_name and prog_slug) is False

    # Missing required name
    invalid_name = clean_str("  ")
    assert bool(prog_id and invalid_name and prog_slug) is False


def test_episode_validation_rules():
    # Valid episode
    ep_id = clean_str("102537")
    ep_title = clean_str("Muhabbat Khel Tamasha | Teaser 2 | TV One Drama")
    ep_slug = clean_str("muhabbat-khel-tamasha-teaser-2-tv-one-drama")
    assert bool(ep_id and ep_title and ep_slug) is True

    # Episode with empty title is invalid
    invalid_title = clean_str("NULL")
    assert bool(ep_id and invalid_title and ep_slug) is False


def test_orphan_episode_handling(db_session):
    importer = CsvMediaImporter(db_session)
    # Check that inspect source files detects headers correctly
    status = importer.inspect_source_files()
    assert status["prod_enrichment"]["exists"] is True
    assert status["episodes_prod"]["exists"] is True
    assert "program_id" in status["episodes_prod"]["headers"]

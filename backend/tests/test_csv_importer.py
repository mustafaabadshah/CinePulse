"""Comprehensive unit and integration tests for CSV ingestion and normalization."""

import os
import pytest
from app.services.data_normalizer import (
    clean_str,
    parse_int,
    parse_float,
    parse_bool,
    parse_duration_seconds,
    split_tags,
)
from app.services.csv_importer import CSVImporter
from app.models.program import Program
from app.models.episode import Episode


def test_normalizer_primitives():
    # String cleaning
    assert clean_str("  Hello World  ") == "Hello World"
    assert clean_str("NULL") is None
    assert clean_str("nan") is None
    assert clean_str("") is None
    assert clean_str(None) is None

    # Number parsing
    assert parse_int("123") == 123
    assert parse_int("  456  ") == 456
    assert parse_int("invalid") is None
    assert parse_int("") is None
    assert parse_int(None) is None

    assert parse_float("12.34") == 12.34
    assert parse_float("invalid") is None

    # Boolean parsing
    assert parse_bool("true") is True
    assert parse_bool("1") is True
    assert parse_bool("Yes") is True
    assert parse_bool("t") is True
    assert parse_bool("false") is False
    assert parse_bool("0") is False
    assert parse_bool("No") is False
    assert parse_bool("f") is False
    assert parse_bool(None) is False

    # Tag splitting
    assert split_tags("Action, Drama, Thriller") == ["Action", "Drama", "Thriller"]
    assert split_tags("Action|Drama|Thriller") == ["Action", "Drama", "Thriller"]
    assert split_tags("SingleTag") == ["SingleTag"]
    assert split_tags("") == []
    assert split_tags(None) == []


def test_duration_parsing():
    # HH:MM:SS format
    assert parse_duration_seconds("01:30:00") == 5400
    assert parse_duration_seconds("00:45:30") == 2730
    # MM:SS format
    assert parse_duration_seconds("15:30") == 930
    # Raw seconds
    assert parse_duration_seconds("3600") == 3600
    # Text format
    assert parse_duration_seconds("1h 30m") == 5400
    assert parse_duration_seconds("45 mins") == 2700
    assert parse_duration_seconds("invalid") is None


def test_csv_importer_inspect_source_files(db_session):
    importer = CSVImporter(db_session)
    status = importer.inspect_source_files()
    assert "prod_enrichment" in status
    assert "episodes_prod" in status

    # Both files must exist and be readable
    pe = status["prod_enrichment"]
    ep = status["episodes_prod"]

    assert pe["exists"] is True
    assert pe["readable"] is True
    assert pe["row_count"] == 634
    assert "id" in pe["headers"]

    assert ep["exists"] is True
    assert ep["readable"] is True
    assert ep["row_count"] == 6547
    assert "id" in ep["headers"]


def test_csv_importer_dry_run_does_not_mutate_db(db_session):
    importer = CSVImporter(db_session)
    report = importer.import_all(dry_run=True, batch_size=500)

    assert report.dry_run is True
    assert report.total_records_processed > 7000
    assert report.programs["rows_read"] == 634
    assert report.episodes["rows_read"] == 6547

    # Ensure no rows were added to the test database session
    program_count = db_session.query(Program).count()
    episode_count = db_session.query(Episode).count()
    assert program_count == 0
    assert episode_count == 0


def test_csv_importer_idempotency(db_session):
    importer = CSVImporter(db_session)
    
    # Run first import
    report1 = importer.import_all(dry_run=False, batch_size=1000)
    assert report1.dry_run is False
    assert report1.records_created > 0
    
    p_count1 = db_session.query(Program).count()
    e_count1 = db_session.query(Episode).count()
    assert p_count1 == 634
    assert e_count1 == 6547

    # Run second import immediately
    report2 = importer.import_all(dry_run=False, batch_size=1000)
    assert report2.records_created == 0
    assert report2.records_updated == 0
    assert report2.programs["unchanged"] == 634
    assert report2.episodes["unchanged"] == 6547

    p_count2 = db_session.query(Program).count()
    e_count2 = db_session.query(Episode).count()
    assert p_count2 == p_count1
    assert e_count2 == e_count1

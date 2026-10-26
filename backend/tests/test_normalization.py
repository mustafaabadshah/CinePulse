"""Unit tests for media catalog normalization and parsing."""

from app.services.data_normalizer import (
    clean_str,
    parse_bool,
    parse_datetime,
    parse_duration_seconds,
    parse_float,
    parse_int,
    split_tags,
)


def test_clean_str():
    assert clean_str("  Tamasha OTT Drama  ") == "Tamasha OTT Drama"
    assert clean_str("NULL") is None
    assert clean_str("None") is None
    assert clean_str("nan") is None
    assert clean_str("") is None
    assert clean_str(None) is None


def test_parse_duration():
    assert parse_duration_seconds("01:45:30") == 6330
    assert parse_duration_seconds("45:30") == 2730
    assert parse_duration_seconds("3600") == 3600
    assert parse_duration_seconds("1h 15m") == 4500
    assert parse_duration_seconds("30 mins") == 1800
    assert parse_duration_seconds("invalid") is None


def test_parse_bool():
    assert parse_bool("true") is True
    assert parse_bool("1") is True
    assert parse_bool("Yes") is True
    assert parse_bool("false") is False
    assert parse_bool("0") is False
    assert parse_bool("No") is False
    assert parse_bool(None, default=False) is False


def test_parse_numbers():
    assert parse_int("1250000") == 1250000
    assert parse_int("1250000.0") == 1250000
    assert parse_int("invalid") is None
    assert parse_float("4.5") == 4.5
    assert parse_float("invalid") is None


def test_split_tags():
    assert split_tags("Action, Thriller, Drama") == ["Action", "Thriller", "Drama"]
    assert split_tags("Comedy|Romance") == ["Comedy", "Romance"]
    assert split_tags("") == []
    assert split_tags(None) == []


def test_parse_datetime():
    dt = parse_datetime("2024-05-15T12:00:00Z")
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 5
    assert dt.day == 15

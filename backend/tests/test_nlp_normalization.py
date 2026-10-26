"""Tests for NLP deterministic Unicode and text normalization helpers."""

import pytest
from app.services.nlp.normalization import canonical_key, normalize_query_text


def test_normalize_query_text_none_and_empty():
    assert normalize_query_text(None) == ""
    assert normalize_query_text("") == ""
    assert normalize_query_text("   ") == ""


def test_normalize_query_text_unicode_nfkc():
    # Combining characters and ligatures
    assert normalize_query_text("ﬁlms") == "films"
    # Special dash variants
    assert normalize_query_text("Ehd\u2013E\u2014Wafa") == "Ehd-E-Wafa"
    assert normalize_query_text("Hum\u2212News") == "Hum-News"
    # Curved quotes
    assert normalize_query_text("“Parizaad”") == '"Parizaad"'
    assert normalize_query_text("‘Ehd E Wafa’") == "'Ehd E Wafa'"


def test_normalize_query_text_whitespace_collapse():
    assert normalize_query_text("  Ehd   E   Wafa   Episode   3  ") == "Ehd E Wafa Episode 3"
    assert normalize_query_text("\tWabaal\nEpisode 1\r") == "Wabaal Episode 1"


def test_canonical_key():
    assert canonical_key("Ehd-E-Wafa") == "ehd e wafa"
    assert canonical_key("“Parizaad”") == "parizaad"
    assert canonical_key("Hum News HD!") == "hum news hd"
    assert canonical_key("  Pakistani   Dramas  ") == "pakistani dramas"
    assert canonical_key(None) == ""

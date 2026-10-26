"""Unit tests for QueryParser entity resolution, episode regex, and filter derivation."""

import pytest
import spacy

from app.services.nlp.catalog_entities import CatalogKnowledgeBase
from app.services.nlp.query_parser import QueryParser
from app.services.nlp.schemas import EntityType


@pytest.fixture
def mock_kb():
    kb = CatalogKnowledgeBase()
    kb.programs_by_key = {
        "ehd e wafa": {"id": "100075", "name": "Ehd E Wafa"},
        "parizaad": {"id": "100080", "name": "Parizaad"},
        "wabaal": {"id": "100090", "name": "Wabaal"},
    }
    kb.channels_by_key = {
        "hum news": "Hum News",
        "tv one": "TV One",
    }
    kb.genres_by_key = {
        "drama": "Drama",
        "comedy": "Comedy",
    }
    kb.languages_by_key = {
        "urdu": "Urdu",
    }
    kb.patterns = [
        {"label": EntityType.PROGRAM_TITLE.value, "pattern": "Ehd E Wafa", "id": "100075"},
        {"label": EntityType.PROGRAM_TITLE.value, "pattern": "Parizaad", "id": "100080"},
        {"label": EntityType.CHANNEL.value, "pattern": "Hum News", "id": "Hum News"},
        {"label": EntityType.GENRE.value, "pattern": "Drama", "id": "Drama"},
    ]
    return kb


@pytest.fixture
def parser_with_spacy(mock_kb):
    nlp = spacy.blank("en")
    ruler = nlp.add_pipe("entity_ruler", config={"phrase_matcher_attr": "LOWER"})
    ruler.add_patterns(mock_kb.patterns)
    return QueryParser(nlp=nlp, kb=mock_kb)


def test_parse_empty_query(parser_with_spacy):
    res = parser_with_spacy.parse("")
    assert res.is_nlp_assisted is False
    assert res.remaining_query == ""
    assert res.inferred_filters == {}


def test_parse_episode_number_formats(parser_with_spacy):
    queries = [
        ("Episode 3", 3),
        ("ep 03", 3),
        ("EP 2", 2),
        ("eps 14", 14),
        ("Part 5", 5),
        ("S01E04", 4),
        ("Season 1 Episode 8", 8),
    ]
    for q, expected_num in queries:
        res = parser_with_spacy.parse(q)
        assert res.episode_number == expected_num
        assert res.is_nlp_assisted is True
        assert res.inferred_filters.get("episode_number") == expected_num


def test_parse_program_and_episode(parser_with_spacy):
    res = parser_with_spacy.parse("Ehd E Wafa Episode 3")
    assert res.is_nlp_assisted is True
    assert res.matched_program_id == "100075"
    assert res.matched_program_name == "Ehd E Wafa"
    assert res.episode_number == 3
    assert res.remaining_query == ""
    assert res.inferred_filters == {
        "program_id": "100075",
        "episode_number": 3,
    }


def test_parse_with_remaining_keywords(parser_with_spacy):
    res = parser_with_spacy.parse("Parizaad episode 5 teaser promo")
    assert res.is_nlp_assisted is True
    assert res.matched_program_id == "100080"
    assert res.episode_number == 5
    assert "teaser promo" in res.remaining_query


def test_parse_channel_entity(parser_with_spacy):
    res = parser_with_spacy.parse("Hum News live transmission")
    assert res.is_nlp_assisted is True
    assert res.matched_channel == "Hum News"
    assert res.remaining_query == "live transmission"
    assert res.inferred_filters.get("channel_name") == "Hum News"


def test_parse_genre_entity(parser_with_spacy):
    res = parser_with_spacy.parse("top Pakistani drama")
    assert res.is_nlp_assisted is True
    assert res.matched_genre == "Drama"
    assert "top Pakistani" in res.remaining_query


def test_parse_graceful_without_spacy(mock_kb):
    parser = QueryParser(nlp=None, kb=mock_kb)
    # Direct dictionary fallback should resolve exact program
    res = parser.parse("Parizaad")
    assert res.matched_program_id == "100080"
    assert res.is_nlp_assisted is True


def test_parse_conversational_funny_movie(mock_kb):
    nlp = spacy.blank("en")
    ruler = nlp.add_pipe("entity_ruler", config={"phrase_matcher_attr": "LOWER"})
    mock_kb.genres_by_key["funny"] = "Comedy"
    mock_kb.content_types_by_key["movie"] = "movie"
    patterns = list(mock_kb.patterns) + [
        {"label": EntityType.GENRE.value, "pattern": "funny", "id": "Comedy"},
        {"label": EntityType.CONTENT_TYPE.value, "pattern": "movie", "id": "movie"},
    ]
    ruler.add_patterns(patterns)
    parser = QueryParser(nlp=nlp, kb=mock_kb)

    res = parser.parse("i want to watch funny movie")
    assert res.is_nlp_assisted is True
    assert res.matched_genre == "Comedy"
    assert res.matched_content_type == "movie"
    assert res.remaining_query == ""
    assert res.inferred_filters.get("genre_list") == "comedy"


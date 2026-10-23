"""Unit tests for validation rules and schema enforcement."""

from app.ingestion.validator import (
    validate_institution_record,
    validate_publication_record,
    validate_researcher_record,
)


def test_validate_institution_success():
    raw = {
        "name": "MIT CSAIL",
        "country": "United States",
        "city": "Cambridge",
        "website_url": "https://www.csail.mit.edu",
    }
    clean, errors = validate_institution_record(raw)
    assert errors == []
    assert clean is not None
    assert clean["name"] == "MIT CSAIL"
    assert clean["country"] == "United States"


def test_validate_institution_missing_required():
    raw = {"country": "United States"}
    clean, errors = validate_institution_record(raw)
    assert len(errors) >= 2
    assert any("name is required" in e.lower() for e in errors)
    assert any("city is required" in e.lower() for e in errors)
    assert clean is None


def test_validate_researcher_verified_email_requires_source():
    # If marked verified, must have contact_source_url
    raw = {
        "full_name": "Dr. Alice Turing",
        "institution_id": "inst_mit",
        "country": "United States",
        "contact_email": "aturing@mit.edu",
        "contact_email_verified": True,
        "contact_source_url": None,  # Missing source URL!
    }
    clean, errors = validate_researcher_record(raw)
    assert len(errors) == 1
    assert "requires an authoritative contact_source_url" in errors[0]
    assert clean is None


def test_validate_researcher_invalid_email_format():
    raw = {
        "full_name": "Dr. Alice Turing",
        "institution_id": "inst_mit",
        "country": "United States",
        "contact_email": "not-an-email",
    }
    clean, errors = validate_researcher_record(raw)
    assert len(errors) == 1
    assert "Invalid email format" in errors[0]


def test_validate_publication_year_bounds():
    raw = {
        "title": "Quantum Foundations",
        "publication_year": 1850,  # Below 1900
        "authors": ["Albert Einstein"],
    }
    clean, errors = validate_publication_record(raw)
    assert len(errors) == 1
    assert "must be between 1900 and 2100" in errors[0]

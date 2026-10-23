"""Input validation rules and schema enforcement for ingestion."""

import re
from typing import Any, Dict, List, Tuple

from app.ingestion.normalizer import normalize_text

EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,63}$")
URL_REGEX = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)


def validate_institution_record(raw: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, List[str]]:
    """Validates and cleans an institution record."""
    errors = []
    name = normalize_text(str(raw.get("name", "")))
    if not name:
        errors.append("Institution name is required and cannot be empty.")

    country = normalize_text(str(raw.get("country", "")))
    if not country:
        errors.append("Institution country is required.")

    city = normalize_text(str(raw.get("city", "")))
    if not city:
        errors.append("Institution city is required.")

    raw_website = raw.get("website_url")
    website_url = (
        str(raw_website).strip() if raw_website is not None and str(raw_website).strip() else None
    )
    if website_url and not URL_REGEX.match(website_url):
        errors.append(f"Invalid website URL format: {website_url}")

    raw_ror = raw.get("ror_id")
    ror_id = str(raw_ror).strip() if raw_ror is not None and str(raw_ror).strip() else None

    if errors:
        return None, errors

    clean = {
        "id": raw.get("id"),  # Will be generated if missing
        "name": name,
        "country": country,
        "city": city,
        "website_url": website_url,
        "ror_id": ror_id,
    }
    return clean, []


def validate_researcher_record(raw: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, List[str]]:
    """Validates and cleans a researcher record."""
    errors = []
    full_name = normalize_text(str(raw.get("full_name", "")))
    if not full_name:
        errors.append("Researcher full_name is required.")

    institution_id = str(raw.get("institution_id", "")).strip()
    if not institution_id:
        errors.append("Researcher institution_id is required.")

    country = normalize_text(str(raw.get("country", "")))
    if not country:
        errors.append("Researcher country is required.")

    # Email verification rule enforcement:
    # Never claim verified contact unless source URL is present
    contact_email_verified = bool(raw.get("contact_email_verified", False))
    raw_email = raw.get("contact_email")
    contact_email = str(raw_email).strip() if raw_email is not None else None

    raw_source_url = raw.get("contact_source_url")
    contact_source_url = str(raw_source_url).strip() if raw_source_url is not None else None

    if contact_email:
        if not EMAIL_REGEX.match(contact_email):
            errors.append(f"Invalid email format: {contact_email}")
        if contact_email_verified and not contact_source_url:
            errors.append(
                "Verified institutional contact email requires an authoritative contact_source_url."
            )

    raw_profile = raw.get("official_profile_url")
    profile_url = str(raw_profile).strip() if raw_profile is not None else None
    if profile_url and not URL_REGEX.match(profile_url):
        errors.append(f"Invalid official profile URL: {profile_url}")

    raw_interests = raw.get("research_interests", [])
    if isinstance(raw_interests, str):
        interests = [normalize_text(i) for i in raw_interests.split(",") if normalize_text(i)]
    elif isinstance(raw_interests, list):
        interests = [normalize_text(str(i)) for i in raw_interests if normalize_text(str(i))]
    else:
        interests = []

    if errors:
        return None, errors

    last_verified = raw.get("last_verified_at")
    if isinstance(last_verified, str) and last_verified.strip():
        try:
            # Handle trailing Z
            iso_str = last_verified.strip().replace("Z", "+00:00")
            from datetime import datetime

            last_verified = datetime.fromisoformat(iso_str)
        except Exception:
            last_verified = None

    clean = {
        "id": raw.get("id"),
        "full_name": full_name,
        "official_profile_url": profile_url,
        "institution_id": institution_id,
        "department": normalize_text(str(raw.get("department", ""))) or None,
        "country": country,
        "research_interests": interests,
        "biography": normalize_text(str(raw.get("biography", ""))) or None,
        "contact_email_verified": contact_email_verified,
        "contact_email": contact_email,
        "contact_source_url": contact_source_url,
        "last_verified_at": last_verified,
        "is_synthetic": bool(raw.get("is_synthetic", False)),
    }
    return clean, []


def validate_publication_record(raw: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, List[str]]:
    """Validates and cleans a publication record."""
    errors = []
    title = normalize_text(str(raw.get("title", "")))
    if not title:
        errors.append("Publication title is required.")

    try:
        year = int(raw.get("publication_year", 0))
        if year < 1900 or year > 2100:
            errors.append(f"Publication year must be between 1900 and 2100. Got: {year}")
    except (ValueError, TypeError):
        errors.append(f"Invalid publication year: {raw.get('publication_year')}")
        year = 0

    raw_authors = raw.get("authors", [])
    if isinstance(raw_authors, str):
        authors = [normalize_text(a) for a in raw_authors.split(",") if normalize_text(a)]
    elif isinstance(raw_authors, list):
        authors = [normalize_text(str(a)) for a in raw_authors if normalize_text(str(a))]
    else:
        authors = []

    if not authors:
        errors.append("Publication must have at least one author.")

    raw_keywords = raw.get("keywords", [])
    if isinstance(raw_keywords, str):
        keywords = [normalize_text(k) for k in raw_keywords.split(",") if normalize_text(k)]
    elif isinstance(raw_keywords, list):
        keywords = [normalize_text(str(k)) for k in raw_keywords if normalize_text(str(k))]
    else:
        keywords = []

    raw_canonical = raw.get("canonical_url")
    canonical_url = (
        str(raw_canonical).strip()
        if raw_canonical is not None and str(raw_canonical).strip()
        else None
    )
    if canonical_url and not URL_REGEX.match(canonical_url):
        errors.append(f"Invalid canonical URL: {canonical_url}")

    raw_doi = raw.get("doi")
    doi = str(raw_doi).strip() if raw_doi is not None and str(raw_doi).strip() else None

    if errors:
        return None, errors

    clean = {
        "id": raw.get("id"),
        "title": title,
        "abstract": normalize_text(str(raw.get("abstract", "") or "")) or None,
        "authors": authors,
        "primary_institution_id": str(raw.get("primary_institution_id", "") or "").strip() or None,
        "publication_year": year,
        "venue": normalize_text(str(raw.get("venue", "") or "")) or None,
        "doi": doi,
        "canonical_url": canonical_url,
        "keywords": keywords,
        "source_provider": str(raw.get("source_provider", "synthetic")).strip(),
        "is_synthetic": bool(raw.get("is_synthetic", False)),
    }
    return clean, []

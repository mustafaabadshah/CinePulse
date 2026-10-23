"""Data normalization and stable identifier generation for ResearchRadar."""

import hashlib
import json
import re
import unicodedata
from typing import Any, Dict


def normalize_text(text: str) -> str:
    """Normalizes whitespace and unicode characters in text."""
    if not text:
        return ""
    # Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", text)
    # Replace multiple whitespace/newlines with single space
    text = re.sub(r"\s+", " ", text).strip()
    return text


def slugify(text: str) -> str:
    """Generates a clean URL- and ID-safe slug from arbitrary text."""
    text = normalize_text(text).lower()
    # Replace non-alphanumeric chars with underscore
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def generate_institution_id(name: str) -> str:
    """Generates a stable ID for an institution, e.g. inst_massachusetts_institute_of_technology."""
    slug = slugify(name)
    return f"inst_{slug[:48]}"


def generate_researcher_id(full_name: str, institution_id: str) -> str:
    """Generates a stable ID for a researcher."""
    name_slug = slugify(full_name)
    inst_suffix = institution_id.replace("inst_", "")[:16]
    return f"res_{name_slug[:36]}_{inst_suffix}"


def generate_publication_id(title: str, year: int, doi: str | None = None) -> str:
    """Generates a stable ID for a publication based on DOI or title+year."""
    if doi and doi.strip():
        # Clean DOI slug
        doi_clean = slugify(doi.strip())
        return f"pub_{doi_clean[:58]}"
    title_slug = slugify(title)
    return f"pub_{year}_{title_slug[:48]}"


def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """Computes a deterministic SHA-256 hash of a payload dictionary for duplicate detection."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

"""Deterministic text and Unicode normalization helpers for CinePulse NLP."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional


# Pre-compiled regex patterns for deterministic normalization
_WHITESPACE_RE = re.compile(r"\s+")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_DASH_VARIANTS_RE = re.compile(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]")
_QUOTE_VARIANTS_RE = re.compile(r"[\u2018\u2019\u201A\u201B]")
_DOUBLE_QUOTE_VARIANTS_RE = re.compile(r"[\u201C\u201D\u201E\u201F]")


def normalize_query_text(text: Optional[str]) -> str:
    """Normalizes query text deterministically for consistent NLP entity matching.
    
    Principles:
    - Safe handling of None, empty, and non-string inputs.
    - NFKC Unicode normalization (normalizes combined characters, ligatures).
    - Replaces typographical dash/quote variants with standard ASCII equivalents.
    - Strips non-printable control characters.
    - Collapses repeated whitespace.
    - Preserves meaningful punctuation and casing (case-insensitivity is applied at matching time).
    
    Examples:
        None -> ""
        "  Ehd-E-Wafa   Episode 3 " -> "Ehd-E-Wafa Episode 3"
        "Pakistani\u2013Dramas" -> "Pakistani-Dramas"
        "“Parizaad”" -> '"Parizaad"'
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # 1. Unicode NFKC normalization
    s = unicodedata.normalize("NFKC", text)

    # 2. Remove control characters
    s = _CONTROL_CHARS_RE.sub(" ", s)

    # 3. Standardize typographical variants to ASCII equivalents
    s = _DASH_VARIANTS_RE.sub("-", s)
    s = _QUOTE_VARIANTS_RE.sub("'", s)
    s = _DOUBLE_QUOTE_VARIANTS_RE.sub('"', s)

    # 4. Collapse consecutive whitespace and strip margins
    s = _WHITESPACE_RE.sub(" ", s).strip()

    return s


def canonical_key(text: Optional[str]) -> str:
    """Computes a lowercased, punctuation-flattened matching key for catalog lookup.
    
    Does NOT modify display text; used exclusively for dictionary and lookup table keys.
    """
    if not text:
        return ""
    norm = normalize_query_text(text).lower()
    # Replace non-alphanumeric separators with a single space
    cleaned = re.sub(r"[^\w\s]", " ", norm)
    return _WHITESPACE_RE.sub(" ", cleaned).strip()

"""Data normalization, parsing, and cleaning helpers for media catalog ingestion."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, List, Optional


def clean_str(val: Any) -> Optional[str]:
    """Cleans a string, converting empty, whitespace-only, or NULL/NaN strings to None."""
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    if s.lower() in ("null", "none", "nan", "nil", "n/a", "undefined"):
        return None
    return s


def parse_bool(val: Any, default: bool = False) -> bool:
    """Parses boolean from various string and numeric formats."""
    if val is None:
        return default
    s = str(val).strip().lower()
    if s in ("1", "true", "yes", "t", "y", "enable", "enabled"):
        return True
    if s in ("0", "false", "no", "f", "n", "disable", "disabled"):
        return False
    return default


def parse_int(val: Any, default: Optional[int] = None) -> Optional[int]:
    """Parses integer safely from string or number."""
    if val is None:
        return default
    s = str(val).strip()
    if not s or s.lower() in ("null", "none", "nan"):
        return default
    try:
        # Handle float strings like "123.0"
        return int(float(s))
    except (ValueError, TypeError):
        return default


def parse_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    """Parses float safely."""
    if val is None:
        return default
    s = str(val).strip()
    if not s or s.lower() in ("null", "none", "nan"):
        return default
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def parse_duration_seconds(val: Any) -> Optional[int]:
    """Parses duration string in HH:MM:SS or MM:SS format into total seconds.
    
    Examples:
        '00:45:06' -> 2706
        '00:00:35' -> 35
        '12:30'    -> 750
    """
    s = clean_str(val)
    if not s:
        return None
    
    # Check text patterns like '1h 30m' or '45 mins'
    h_match = re.search(r"(\d+)\s*h(?:ours?|rs?)?", s, re.IGNORECASE)
    m_match = re.search(r"(\d+)\s*m(?:in(?:ute)?s?)?", s, re.IGNORECASE)
    s_match = re.search(r"(\d+)\s*s(?:ec(?:ond)?s?)?", s, re.IGNORECASE)
    if h_match or m_match or s_match:
        h = int(h_match.group(1)) if h_match else 0
        m = int(m_match.group(1)) if m_match else 0
        sec = int(s_match.group(1)) if s_match else 0
        return h * 3600 + m * 60 + sec

    # Remove any extra characters or whitespace
    parts = s.split(":")
    try:
        if len(parts) == 3:
            h, m, sec = int(parts[0]), int(parts[1]), int(float(parts[2]))
            return h * 3600 + m * 60 + sec
        elif len(parts) == 2:
            m, sec = int(parts[0]), int(float(parts[1]))
            return m * 60 + sec
        elif len(parts) == 1 and parts[0].isdigit():
            return int(parts[0])
    except (ValueError, TypeError):
        return None
    return None


def parse_datetime(val: Any) -> Optional[datetime]:
    """Parses datetime safely from ISO or date string."""
    s = clean_str(val)
    if not s:
        return None
    try:
        # Replace trailing Z with UTC timezone
        cleaned = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        # Fallback date pattern YYYY-MM-DD
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
            except ValueError:
                return None
    return None


def split_tags(val: Optional[str]) -> List[str]:
    """Splits a comma- or pipe-separated string into a clean list of unique tag strings."""
    if not val:
        return []
    # Replace pipes and semicolons with commas
    unified = val.replace("|", ",").replace(";", ",")
    raw_tags = [t.strip() for t in unified.split(",")]
    seen = set()
    tags = []
    for t in raw_tags:
        if t and t.lower() not in seen:
            seen.add(t.lower())
            tags.append(t)
    return tags

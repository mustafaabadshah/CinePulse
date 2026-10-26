"""Data normalization, parsing, and cleaning helpers for media catalog ingestion."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, List, Optional

TAMASHA_S3_BASE_URL = "https://tamasha-app-images.s3.amazonaws.com/jazzlive/"


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


_EPISODE_PATTERNS = [
    # Explicit episode or ep: "Episode 1", "Episode 01", "Ep 03", "Ep. 04", "Ep: 5", "EP06", "Teaser 2"
    re.compile(r"(?:episode|ep|part|teaser|promo)\.?\s*[:#\-_|]?\s*(\d+)", re.IGNORECASE),
    # Season / Episode: "S01E02", "S1 E2"
    re.compile(r"\bs?\d+\s*[ex]\s*(\d+)\b", re.IGNORECASE),
    # Words with trailing number: "Muhabbat Khel Tamasha - 3"
    re.compile(r"\b(?:e|ep|part)\s*(\d+)\b", re.IGNORECASE),
]


def extract_episode_number(title: Optional[str], slug: Optional[str] = None) -> Optional[int]:
    """Extracts chronological episode sequence number from media title or slug.
    
    Examples:
        'Parizaad Ep 01' -> 1
        'Ehd E Wafa | Episode 25' -> 25
        'Jahan Fans Wahan Stadium - Episode 03' -> 3
        'Muhabbat Khel Tamasha | Teaser 2' -> 2
    """
    for text in (title, slug):
        if not text:
            continue
        cleaned = clean_str(text)
        if not cleaned:
            continue
        for pat in _EPISODE_PATTERNS:
            m = pat.search(cleaned)
            if m:
                try:
                    num = int(m.group(1))
                    if 0 < num < 10000:
                        return num
                except (ValueError, TypeError):
                    continue
    return None


def parse_duration_seconds(val: Any) -> Optional[int]:
    """Parses duration string in HH:MM:SS, MM:SS, or pure integer format into total seconds.
    
    Examples:
        '00:45:06' -> 2706
        '00:00:35' -> 35
        '12:30'    -> 750
        '1538'     -> 1538
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
        total = h * 3600 + m * 60 + sec
        return total if total >= 0 else None

    # Handle pure numeric seconds (integer or float string)
    if re.fullmatch(r"^\d+(\.\d+)?$", s):
        sec = int(float(s))
        return sec if sec >= 0 else None

    # Colon-separated time format
    parts = s.split(":")
    try:
        if len(parts) == 3:
            h = int(parts[0])
            m = int(parts[1])
            sec = int(float(parts[2]))
            if h < 0 or m < 0 or sec < 0:
                return None
            return h * 3600 + m * 60 + sec
        elif len(parts) == 2:
            m = int(parts[0])
            sec = int(float(parts[1]))
            if m < 0 or sec < 0:
                return None
            return m * 60 + sec
    except (ValueError, TypeError):
        return None
    return None


def format_duration_clock(seconds: Optional[int]) -> Optional[str]:
    """Converts numeric seconds into standard clock format (MM:SS or HH:MM:SS).
    
    Examples:
        39   -> '00:39'
        2370 -> '39:30'
        4779 -> '01:19:39'
    """
    if seconds is None or seconds < 0:
        return None
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def normalize_thumbnail_url(val: Any) -> Optional[str]:
    """Resolves relative thumbnail paths to the canonical Amazon S3 CDN URL.
    
    Examples:
        'uploads/episodes/PgP658VykOd.webp' -> 'https://tamasha-app-images.s3.amazonaws.com/jazzlive/uploads/episodes/PgP658VykOd.webp'
        'https://srv2.jazztv.pk/jazzlive/uploads/...' -> 'https://tamasha-app-images.s3.amazonaws.com/jazzlive/uploads/...'
        'https://tamasha-app-images.s3.amazonaws.com/...' -> unchanged
    """
    s = clean_str(val)
    if not s or s.lower() in ("nothumbnail", "no_thumbnail", "no-thumbnail", "null", "none"):
        return None
    
    # Handle relative paths from episodes_prod.csv
    if s.startswith("uploads/"):
        return f"{TAMASHA_S3_BASE_URL}{s}"
    if s.startswith("/uploads/"):
        return f"{TAMASHA_S3_BASE_URL}{s.lstrip('/')}"
    
    # Migrate legacy offline domain to active S3 bucket
    if s.startswith("https://srv2.jazztv.pk/jazzlive/"):
        return s.replace("https://srv2.jazztv.pk/jazzlive/", TAMASHA_S3_BASE_URL)
    if s.startswith("http://srv2.jazztv.pk/jazzlive/"):
        return s.replace("http://srv2.jazztv.pk/jazzlive/", TAMASHA_S3_BASE_URL)

    return s


def parse_datetime(val: Any) -> Optional[datetime]:
    """Parses datetime safely from ISO or date string."""
    s = clean_str(val)
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        pass
    
    # Fallback to date patterns like YYYY-MM-DD
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%b-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def split_tags(val: Any, delimiter: Optional[str] = None) -> List[str]:
    """Splits comma, pipe, or delimiter separated tags, stripping whitespace."""
    s = clean_str(val)
    if not s:
        return []
    if delimiter:
        raw_items = s.split(delimiter)
    else:
        raw_items = re.split(r"[,|;]", s)
    tags = [t.strip() for t in raw_items if t.strip()]
    return list(dict.fromkeys(tags))

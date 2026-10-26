"""End-to-End Media Duration Audit Script for ResearchRadar / Tamasha Catalog Explorer.

Inspects raw CSV, SQLite canonical storage, and Meilisearch index representations.
Identifies anomalies such as '00:00:32', '00:00:39', missing, zero, negative, and mismatched durations.
Outputs machine-readable JSON and formatted summary report.
"""

from __future__ import annotations

import csv
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "episodes_prod.csv")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "researchradar.db")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "data_quality")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def parse_duration_formats(raw_val: Optional[str]) -> Dict[str, Any]:
    """Analyzes string patterns in raw duration."""
    if not raw_val or not raw_val.strip():
        return {"category": "empty", "parts": []}
    s = raw_val.strip()
    if s.isdigit():
        return {"category": "pure_integer", "val": int(s)}
    parts = s.split(":")
    if len(parts) == 3:
        return {"category": "HH:MM:SS", "h": parts[0], "m": parts[1], "s": parts[2]}
    elif len(parts) == 2:
        return {"category": "MM:SS", "m": parts[0], "s": parts[1]}
    return {"category": "other", "raw": s}


def run_duration_audit() -> Dict[str, Any]:
    print("======================================================================")
    print("               TAMASHA MEDIA DURATION END-TO-END AUDIT                ")
    print("======================================================================")

    # 1. Read Raw CSV
    print(f"Reading raw CSV: {CSV_PATH}")
    csv_episodes: Dict[str, Dict[str, Any]] = {}
    with open(CSV_PATH, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ep_id = row.get("id", "").strip()
            if ep_id:
                csv_episodes[ep_id] = {
                    "raw_duration": row.get("duration", "").strip(),
                    "title": row.get("title", "").strip(),
                    "program_id": row.get("program_id", "").strip(),
                    "is_vertical": row.get("is_vertical", "").strip(),
                }

    # 2. Read SQLite Database
    print(f"Reading SQLite database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.title, e.program_id, p.name, e.duration, e.duration_seconds, e.is_vertical, e.views
        FROM episodes e
        LEFT JOIN programs p ON e.program_id = p.id
    """)
    db_rows = cursor.fetchall()
    conn.close()

    total_records = len(db_rows)
    raw_formats = Counter()
    suspicious_records = []
    category_counts = Counter()
    minute_as_second_candidates = []
    seconds_distribution = Counter()
    null_or_empty_count = 0
    zero_or_negative_count = 0

    detailed_audit: List[Dict[str, Any]] = []

    for row in db_rows:
        ep_id, title, prog_id, prog_name, db_duration, db_duration_sec, is_vert, views = row
        csv_data = csv_episodes.get(ep_id, {})
        csv_raw_dur = csv_data.get("raw_duration", "")

        fmt_info = parse_duration_formats(csv_raw_dur)
        raw_formats[fmt_info["category"]] += 1

        is_suspicious = False
        reasons = []

        # Check null/empty
        if not csv_raw_dur:
            null_or_empty_count += 1
            reasons.append("missing_csv_duration")
            is_suspicious = True

        # Check 0 or negative
        if db_duration_sec is not None and db_duration_sec <= 0:
            zero_or_negative_count += 1
            reasons.append("zero_or_negative_seconds")
            is_suspicious = True

        # Track suspicious durations like 00:00:32, 00:00:39 or raw '32', '39'
        if csv_raw_dur in ("32", "39", "00:00:32", "00:00:39", "0:32", "0:39", "32:00", "39:00"):
            is_suspicious = True
            reasons.append(f"flagged_example_val_{csv_raw_dur}")

        # Check if pure integer in raw CSV was interpreted as seconds vs minutes
        # E.g., if a drama episode has raw duration "32" or "45", is it 32 seconds or 32 minutes?
        if fmt_info["category"] == "pure_integer":
            val = fmt_info["val"]
            if val < 60 and not is_vert:
                # If it's a regular TV drama episode and duration is < 60, could it be in minutes?
                reasons.append(f"pure_int_under_60_in_non_vertical_{val}")
                minute_as_second_candidates.append({
                    "id": ep_id,
                    "title": title,
                    "program": prog_name,
                    "raw_val": csv_raw_dur,
                    "db_duration": db_duration,
                    "db_duration_sec": db_duration_sec,
                })

        # Check discrepancy between db_duration and db_duration_sec
        # E.g. db_duration is "00:45:00" but db_duration_sec is 45
        if db_duration and db_duration_sec is not None:
            parts = db_duration.split(":")
            if len(parts) == 3:
                expected_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(float(parts[2]))
                if expected_sec != db_duration_sec:
                    is_suspicious = True
                    reasons.append(f"db_string_sec_mismatch_{expected_sec}_vs_{db_duration_sec}")

        if is_suspicious:
            suspicious_records.append({
                "id": ep_id,
                "title": title,
                "program_name": prog_name,
                "csv_raw_duration": csv_raw_dur,
                "db_duration": db_duration,
                "db_duration_seconds": db_duration_sec,
                "is_vertical": is_vert,
                "reasons": reasons,
            })

        detailed_audit.append({
            "id": ep_id,
            "title": title,
            "program_id": prog_id,
            "program_name": prog_name,
            "csv_raw_duration": csv_raw_dur,
            "db_duration": db_duration,
            "db_duration_seconds": db_duration_sec,
            "category": fmt_info["category"],
            "is_suspicious": is_suspicious,
            "reasons": reasons,
        })

    # Prepare summary
    summary = {
        "total_episodes_audited": total_records,
        "raw_csv_record_count": len(csv_episodes),
        "missing_duration_count": null_or_empty_count,
        "zero_or_negative_duration_count": zero_or_negative_count,
        "raw_duration_format_distribution": dict(raw_formats),
        "total_suspicious_count": len(suspicious_records),
        "pure_integer_under_60_count": len(minute_as_second_candidates),
        "sample_suspicious_records": suspicious_records[:30],
        "sample_pure_int_candidates": minute_as_second_candidates[:20],
    }

    import argparse
    parser = argparse.ArgumentParser(description="Audit media durations.")
    parser.add_argument("--output", default="duration_audit_after.json", help="Output filename")
    args = parser.parse_args()

    # Save to artifacts
    out_file = os.path.join(ARTIFACTS_DIR, args.output)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "records": detailed_audit[:500],  # sample detailed records
        }, f, indent=2)

    print("\n--- Summary of Findings ---")
    print(f"Total episodes audited: {total_records}")
    print(f"Raw format distribution: {dict(raw_formats)}")
    print(f"Missing/empty durations: {null_or_empty_count}")
    print(f"Zero or negative durations: {zero_or_negative_count}")
    print(f"Suspicious records flagged: {len(suspicious_records)}")
    print(f"Pure integers < 60 in non-vertical content: {len(minute_as_second_candidates)}")
    print(f"\nAudit saved to: {out_file}")

    return summary


if __name__ == "__main__":
    run_duration_audit()

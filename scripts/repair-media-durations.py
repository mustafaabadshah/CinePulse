#!/usr/bin/env python3
"""Repeatable, auditable duration repair script for ResearchRadar Tamasha catalog.

Usage:
    python scripts/repair-media-durations.py --dry-run
    python scripts/repair-media-durations.py --apply
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.config import settings
from app.services.data_normalizer import format_duration_clock, parse_duration_seconds
from app.search.client import get_meilisearch_client
from app.services.meilisearch_indexer import rebuild_media_indexes_from_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = Path(settings.database_url.replace("sqlite:///", ""))
CSV_EPISODES = BASE_DIR / "data" / "episodes_prod.csv"
CSV_PROGRAMS = BASE_DIR / "data" / "prod_enrichment.csv"
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "data_quality"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def get_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def repair_durations(dry_run: bool = True) -> Dict[str, Any]:
    print(f"=== Duration Normalization Repair (Mode: {'DRY-RUN' if dry_run else 'APPLY'}) ===")
    
    # Verify CSV immutability baseline
    csv_episodes_hash_before = get_file_sha256(CSV_EPISODES)
    csv_programs_hash_before = get_file_sha256(CSV_PROGRAMS)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, duration, duration_seconds FROM episodes")
    rows = cursor.fetchall()
    total_episodes = len(rows)

    deterministic_repairs: List[Dict[str, Any]] = []
    ambiguous_records: List[Dict[str, Any]] = []
    already_clean = 0

    for r in rows:
        ep_id = r["id"]
        title = r["title"]
        curr_duration = r["duration"]
        curr_seconds = r["duration_seconds"]

        # Check if duration is a pure integer string (e.g. '1538')
        if curr_duration and curr_duration.strip().isdigit():
            sec_val = int(curr_duration.strip())
            new_clock = format_duration_clock(sec_val)
            deterministic_repairs.append({
                "id": ep_id,
                "title": title,
                "old_duration": curr_duration,
                "new_duration": new_clock,
                "old_duration_seconds": curr_seconds,
                "new_duration_seconds": sec_val,
                "reason": "Pure integer seconds normalized to standard MM:SS clock format",
                "confidence": 1.0,
            })
        elif curr_duration is None or curr_duration.strip() == "":
            ambiguous_records.append({
                "id": ep_id,
                "title": title,
                "duration": curr_duration,
                "reason": "Null or empty duration in source catalog - preserved as missing",
            })
        else:
            already_clean += 1

    print(f"Total episodes inspected: {total_episodes}")
    print(f"Already clean / standardized: {already_clean}")
    print(f"Deterministic repairs identified: {len(deterministic_repairs)}")
    print(f"Ambiguous / null records left unchanged: {len(ambiguous_records)}")

    if not dry_run and deterministic_repairs:
        print("\nApplying updates to SQLite database...")
        update_query = """
            UPDATE episodes 
            SET duration = ?, duration_seconds = ?, updated_at = ?
            WHERE id = ?
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        update_params = [
            (rep["new_duration"], rep["new_duration_seconds"], now_iso, rep["id"])
            for rep in deterministic_repairs
        ]
        cursor.executemany(update_query, update_params)
        conn.commit()
        print(f"Successfully updated {len(deterministic_repairs)} records in SQLite.")

        # Reindex Meilisearch
        print("\nReconciling Meilisearch indexes from updated database...")
        try:
            client = get_meilisearch_client()
            engine = create_engine(settings.database_url)
            SessionLocal = sessionmaker(bind=engine)
            with SessionLocal() as db_session:
                reindex_report = rebuild_media_indexes_from_db(db_session, client)
            print(f"Meilisearch reindex status: {reindex_report.get('status')}")
        except Exception as e:
            print(f"Meilisearch reindex error: {e}")
    else:
        print("\n[DRY RUN] No database records were modified.")

    conn.close()

    # Verify CSV files remained unchanged
    csv_episodes_hash_after = get_file_sha256(CSV_EPISODES)
    csv_programs_hash_after = get_file_sha256(CSV_PROGRAMS)
    csv_unmodified = (
        csv_episodes_hash_before == csv_episodes_hash_after
        and csv_programs_hash_before == csv_programs_hash_after
    )

    result_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "dry_run" if dry_run else "apply",
        "total_episodes": total_episodes,
        "already_clean_count": already_clean,
        "deterministic_repairs_count": len(deterministic_repairs),
        "ambiguous_count": len(ambiguous_records),
        "source_csv_unmodified": csv_unmodified,
        "deterministic_repairs": deterministic_repairs,
        "sample_ambiguous": ambiguous_records[:10],
    }

    report_path = ARTIFACTS_DIR / ("duration_repair_dry_run.json" if dry_run else "duration_repair_applied.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result_report, f, indent=2)
    print(f"\nRepair report saved to: {report_path}")

    return result_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repair media durations safely.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Perform read-only dry run inspection")
    group.add_argument("--apply", action="store_true", help="Apply deterministic repairs to SQLite and Meilisearch")
    args = parser.parse_args()

    repair_durations(dry_run=args.dry_run)

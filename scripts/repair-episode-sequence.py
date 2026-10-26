#!/usr/bin/env python3
"""Auditable Episode Number & Sequence Normalization Script.

Populates the canonical `episode_number` integer column in SQLite from media titles
and slugs (e.g. 'Parizaad Ep 01' -> 1, 'Ehd E Wafa | Episode 25' -> 25), enabling
strictly chronological episode sequencing for programs and series.

Usage:
    python scripts/repair-episode-sequence.py --dry-run
    python scripts/repair-episode-sequence.py --apply
"""

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.config import settings
from app.search.client import get_meilisearch_client
from app.services.data_normalizer import extract_episode_number
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


def repair_episode_sequence(dry_run: bool = True) -> Dict[str, Any]:
    print(f"=== Episode Number & Sequence Repair (Mode: {'DRY-RUN' if dry_run else 'APPLY'}) ===")

    csv_episodes_hash_before = get_file_sha256(CSV_EPISODES)
    csv_programs_hash_before = get_file_sha256(CSV_PROGRAMS)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, slug, episode_number, program_id FROM episodes")
    rows = cursor.fetchall()
    total_episodes = len(rows)

    repairs: List[Dict[str, Any]] = []
    unresolved: List[Dict[str, Any]] = []

    for r in rows:
        ep_id = r["id"]
        title = r["title"]
        slug = r["slug"]
        curr_ep_num = r["episode_number"]
        prog_id = r["program_id"]

        extracted = extract_episode_number(title, slug)
        if extracted is not None:
            repairs.append({
                "id": ep_id,
                "title": title,
                "program_id": prog_id,
                "old_episode_number": curr_ep_num,
                "new_episode_number": extracted,
                "confidence": 1.0,
            })
        else:
            unresolved.append({
                "id": ep_id,
                "title": title,
                "program_id": prog_id,
                "reason": "No explicit episode number pattern found in title or slug",
            })

    print(f"Total episodes inspected: {total_episodes}")
    print(f"Episodes with sequence numbers extracted: {len(repairs)} ({round(len(repairs)/total_episodes*100, 1)}%)")
    print(f"Episodes left unchanged: {len(unresolved)} ({round(len(unresolved)/total_episodes*100, 1)}%)")

    if not dry_run and repairs:
        print("\nApplying episode_number updates to SQLite database...")
        update_query = """
            UPDATE episodes
            SET episode_number = ?, updated_at = ?
            WHERE id = ?
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        update_params = [
            (rep["new_episode_number"], now_iso, rep["id"])
            for rep in repairs
        ]
        cursor.executemany(update_query, update_params)
        conn.commit()
        print(f"Successfully updated {len(repairs)} records in SQLite.")

        # Rebuild Meilisearch index with updated episode_number
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
        "extracted_sequence_count": len(repairs),
        "unresolved_count": len(unresolved),
        "source_csv_unmodified": csv_unmodified,
        "sample_repairs": repairs[:25],
        "sample_unresolved": unresolved[:15],
    }

    report_path = ARTIFACTS_DIR / ("sequence_repair_dry_run.json" if dry_run else "sequence_repair_applied.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result_report, f, indent=2)
    print(f"\nSequence repair report saved to: {report_path}")

    return result_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repair episode sequence numbers.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Perform read-only dry run inspection")
    group.add_argument("--apply", action="store_true", help="Apply episode_number repairs to SQLite and Meilisearch")
    args = parser.parse_args()

    repair_episode_sequence(dry_run=args.dry_run)

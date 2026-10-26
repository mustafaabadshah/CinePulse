"""Safe, idempotent CSV ingestion pipeline for media catalog programs and episodes."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from meilisearch import Client
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.episode import Episode
from app.models.import_job import ImportJob
from app.models.program import Program
from app.services.data_normalizer import (
    clean_str,
    parse_bool,
    parse_datetime,
    parse_duration_seconds,
    parse_float,
    parse_int,
)
from app.services.meilisearch_indexer import (
    setup_media_indexes,
    sync_episodes_to_index,
    sync_programs_to_index,
    wait_for_meili_tasks,
)


def detect_file_encoding(filepath: str) -> str:
    """Detects encoding safely, checking for UTF-8 BOM, UTF-16, and valid UTF-8."""
    with open(filepath, "rb") as f:
        header = f.read(4)
        if header.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"
        elif header.startswith(b"\xff\xfe"):
            return "utf-16-le"
        elif header.startswith(b"\xfe\xff"):
            return "utf-16-be"

    # Test reading as utf-8
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for _ in range(100):
                if not f.readline():
                    break
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def detect_file_delimiter(filepath: str, encoding: str) -> str:
    """Detects CSV delimiter with safe fallback to comma."""
    try:
        with open(filepath, "r", encoding=encoding, errors="replace") as f:
            sample = f.read(8192)
            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
            return dialect.delimiter
    except Exception:
        return ","


def compute_record_hash(data: Dict[str, Any]) -> str:
    """Computes a deterministic hash of a record dict to determine if contents changed."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ImportReportDict(dict):
    """Dictionary that also allows attribute-style access."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'ImportReportDict' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class CsvMediaImporter:
    """Service to safely ingest prod_enrichment.csv and episodes_prod.csv."""

    def __init__(self, db: Session, client: Optional[Client] = None):
        self.db = db
        self.client = client

    def inspect_source_files(
        self,
        data_dir: Optional[str] = None,
        enrichment_filename: str = "prod_enrichment.csv",
        episodes_filename: str = "episodes_prod.csv",
    ) -> Dict[str, Any]:
        """Inspects source CSV files reporting status, counts, and headers."""
        from app.config import settings

        d = data_dir or settings.csv_data_dir
        p_path = os.path.abspath(os.path.join(d, enrichment_filename))
        e_path = os.path.abspath(os.path.join(d, episodes_filename))

        def _inspect(path: str) -> Dict[str, Any]:
            if not os.path.exists(path) or not os.path.isfile(path):
                return {"exists": False, "readable": False, "row_count": 0, "headers": []}
            enc = detect_file_encoding(path)
            delim = detect_file_delimiter(path, enc)
            with open(path, "r", encoding=enc, errors="replace") as f:
                reader = csv.reader(f, delimiter=delim)
                try:
                    headers = next(reader)
                except StopIteration:
                    headers = []
                count = sum(1 for _ in reader)
            return {
                "exists": True,
                "readable": True,
                "row_count": count,
                "headers": headers,
                "encoding": enc,
                "delimiter": delim,
            }

        return {
            "prod_enrichment": _inspect(p_path),
            "episodes_prod": _inspect(e_path),
        }

    def import_all(
        self,
        dry_run: bool = False,
        batch_size: int = 500,
        data_dir: Optional[str] = None,
    ) -> ImportReportDict:
        """Convenience method to import all media files."""
        from app.config import settings

        d = data_dir or settings.csv_data_dir
        return self.run_import(data_dir=d, dry_run=dry_run, batch_size=batch_size)

    def validate_files(
        self, data_dir: str, enrichment_filename: str = "prod_enrichment.csv", episodes_filename: str = "episodes_prod.csv"
    ) -> Tuple[str, str]:
        """Validates that both CSV files exist and are readable."""
        enrichment_path = os.path.abspath(os.path.join(data_dir, enrichment_filename))
        episodes_path = os.path.abspath(os.path.join(data_dir, episodes_filename))

        if not os.path.exists(enrichment_path) or not os.path.isfile(enrichment_path):
            raise FileNotFoundError(f"Enrichment file not found at: {enrichment_path}")
        if not os.path.exists(episodes_path) or not os.path.isfile(episodes_path):
            raise FileNotFoundError(f"Episodes file not found at: {episodes_path}")

        return enrichment_path, episodes_path

    def run_import(
        self,
        data_dir: str,
        dry_run: bool = False,
        batch_size: int = 500,
        enrichment_filename: str = "prod_enrichment.csv",
        episodes_filename: str = "episodes_prod.csv",
    ) -> ImportReportDict:
        """Runs the complete ingestion pipeline with dry-run support, idempotency, and Meilisearch sync."""
        start_time = datetime.now(timezone.utc)
        job_id = str(uuid.uuid4())

        enrichment_path, episodes_path = self.validate_files(data_dir, enrichment_filename, episodes_filename)

        # Create persistent job tracking record
        job = ImportJob(
            id=job_id,
            source_name=f"{enrichment_filename} + {episodes_filename}",
            dry_run=dry_run,
            status="running",
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            meili_task_ids=[],
            started_at=start_time,
        )
        if not dry_run:
            self.db.add(job)
            self.db.commit()

        report = ImportReportDict({
            "job_id": job_id,
            "status": "running",
            "dry_run": dry_run,
            "started_at": start_time.isoformat(),
            "sources": {
                "enrichment_file": enrichment_path,
                "episodes_file": episodes_path,
            },
            "programs": {
                "rows_read": 0,
                "inserted": 0,
                "updated": 0,
                "unchanged": 0,
                "rejected": 0,
                "invalid_samples": [],
            },
            "episodes": {
                "rows_read": 0,
                "inserted": 0,
                "updated": 0,
                "unchanged": 0,
                "rejected": 0,
                "with_valid_program": 0,
                "orphan_episodes": 0,
                "invalid_samples": [],
            },
            "meilisearch": {
                "submitted_tasks": [],
                "task_status": "skipped" if dry_run else "pending",
                "indexed_documents": 0,
            },
            "errors": [],
        })

        try:
            # -------------------------------------------------------------
            # STEP 1: Ingest Programs (prod_enrichment.csv)
            # -------------------------------------------------------------
            enc_prog = detect_file_encoding(enrichment_path)
            delim_prog = detect_file_delimiter(enrichment_path, enc_prog)
            logger.info(f"Importing programs from {enrichment_path} (encoding={enc_prog}, delim={delim_prog})")

            # Load existing programs into memory map for comparison
            existing_programs: Dict[str, Program] = {p.id: p for p in self.db.query(Program).all()}
            seen_program_ids: Set[str] = set()
            programs_to_index: List[Program] = []

            with open(enrichment_path, "r", encoding=enc_prog, errors="replace") as f:
                reader = csv.DictReader(f, delimiter=delim_prog)
                for row_idx, row in enumerate(reader, start=1):
                    report["programs"]["rows_read"] += 1
                    raw_id = clean_str(row.get("id"))
                    name = clean_str(row.get("name"))
                    slug = clean_str(row.get("slug"))

                    if not raw_id or not name or not slug:
                        report["programs"]["rejected"] += 1
                        if len(report["programs"]["invalid_samples"]) < 10:
                            report["programs"]["invalid_samples"].append(
                                {"row": row_idx, "id": raw_id, "error": "Missing required field (id, name, or slug)"}
                            )
                        continue

                    if raw_id in seen_program_ids:
                        report["programs"]["rejected"] += 1
                        continue
                    seen_program_ids.add(raw_id)

                    prog_type = clean_str(row.get("type")) or "program"
                    channel_name = clean_str(row.get("channel_name"))
                    info_language = clean_str(row.get("info_language"))
                    info_genre = clean_str(row.get("info_genre"))
                    info_meta_keywords = clean_str(row.get("info_meta_keywords"))
                    info_content_type = clean_str(row.get("info_content_type"))
                    info_staring = clean_str(row.get("info_staring"))

                    existing = existing_programs.get(raw_id)
                    if existing:
                        # Check if any field changed
                        changed = (
                            existing.name != name
                            or existing.slug != slug
                            or existing.type != prog_type
                            or existing.channel_name != channel_name
                            or existing.info_language != info_language
                            or existing.info_genre != info_genre
                            or existing.info_meta_keywords != info_meta_keywords
                            or existing.info_content_type != info_content_type
                            or existing.info_staring != info_staring
                        )
                        if changed:
                            report["programs"]["updated"] += 1
                            if not dry_run:
                                existing.name = name
                                existing.slug = slug
                                existing.type = prog_type
                                existing.channel_name = channel_name
                                existing.info_language = info_language
                                existing.info_genre = info_genre
                                existing.info_meta_keywords = info_meta_keywords
                                existing.info_content_type = info_content_type
                                existing.info_staring = info_staring
                                existing.updated_at = datetime.now(timezone.utc)
                                programs_to_index.append(existing)
                        else:
                            report["programs"]["unchanged"] += 1
                    else:
                        report["programs"]["inserted"] += 1
                        new_prog = Program(
                            id=raw_id,
                            type=prog_type,
                            name=name,
                            slug=slug,
                            channel_name=channel_name,
                            info_language=info_language,
                            info_genre=info_genre,
                            info_meta_keywords=info_meta_keywords,
                            info_content_type=info_content_type,
                            info_staring=info_staring,
                            source_file=enrichment_filename,
                            imported_at=datetime.now(timezone.utc),
                        )
                        existing_programs[raw_id] = new_prog
                        if not dry_run:
                            self.db.add(new_prog)
                            programs_to_index.append(new_prog)

            if not dry_run:
                self.db.flush()

            # -------------------------------------------------------------
            # STEP 2: Ingest Episodes (episodes_prod.csv)
            # -------------------------------------------------------------
            enc_ep = detect_file_encoding(episodes_path)
            delim_ep = detect_file_delimiter(episodes_path, enc_ep)
            logger.info(f"Importing episodes from {episodes_path} (encoding={enc_ep}, delim={delim_ep})")

            # Load existing episode IDs and data into memory
            existing_episodes: Dict[str, Episode] = {e.id: e for e in self.db.query(Episode).all()}
            known_program_ids = set(existing_programs.keys())
            seen_episode_ids: Set[str] = set()
            episodes_to_index: List[Episode] = []

            with open(episodes_path, "r", encoding=enc_ep, errors="replace") as f:
                reader = csv.DictReader(f, delimiter=delim_ep)
                for row_idx, row in enumerate(reader, start=1):
                    report["episodes"]["rows_read"] += 1
                    ep_id = clean_str(row.get("id"))
                    title = clean_str(row.get("title"))
                    slug = clean_str(row.get("slug"))

                    if not ep_id or not title or not slug:
                        report["episodes"]["rejected"] += 1
                        if len(report["episodes"]["invalid_samples"]) < 10:
                            report["episodes"]["invalid_samples"].append(
                                {"row": row_idx, "id": ep_id, "error": "Missing required field (id, title, or slug)"}
                            )
                        continue

                    if ep_id in seen_episode_ids:
                        report["episodes"]["rejected"] += 1
                        continue
                    seen_episode_ids.add(ep_id)

                    raw_prog_id = clean_str(row.get("program_id"))
                    prog_fk = raw_prog_id if raw_prog_id in known_program_ids else None

                    if prog_fk:
                        report["episodes"]["with_valid_program"] += 1
                    else:
                        report["episodes"]["orphan_episodes"] += 1

                    duration_str = clean_str(row.get("duration"))
                    duration_sec = parse_duration_seconds(duration_str)
                    views = parse_int(row.get("views"), default=0) or 0
                    is_enable = parse_bool(row.get("is_enable"), default=True)
                    is_free = parse_bool(row.get("is_free"), default=True)
                    channel_status = parse_bool(row.get("channel_status"), default=True)
                    content_tier = clean_str(row.get("content_tier"))
                    genre = clean_str(row.get("genre"))
                    region = clean_str(row.get("region"))
                    is_vertical = clean_str(row.get("is_vertical"))
                    thumbnail = clean_str(row.get("thumbnail"))
                    description = clean_str(row.get("description"))

                    existing_ep = existing_episodes.get(ep_id)
                    if existing_ep:
                        changed = (
                            existing_ep.title != title
                            or existing_ep.slug != slug
                            or existing_ep.program_id != prog_fk
                            or existing_ep.raw_program_id != raw_prog_id
                            or existing_ep.duration != duration_str
                            or existing_ep.duration_seconds != duration_sec
                            or existing_ep.views != views
                            or existing_ep.is_enable != is_enable
                            or existing_ep.is_free != is_free
                            or existing_ep.content_tier != content_tier
                            or existing_ep.genre != genre
                            or existing_ep.region != region
                            or existing_ep.is_vertical != is_vertical
                            or existing_ep.thumbnail != thumbnail
                            or existing_ep.description != description
                        )
                        if changed:
                            report["episodes"]["updated"] += 1
                            if not dry_run:
                                existing_ep.title = title
                                existing_ep.slug = slug
                                existing_ep.program_id = prog_fk
                                existing_ep.raw_program_id = raw_prog_id
                                existing_ep.duration = duration_str
                                existing_ep.duration_seconds = duration_sec
                                existing_ep.views = views
                                existing_ep.is_enable = is_enable
                                existing_ep.is_free = is_free
                                existing_ep.channel_status = channel_status
                                existing_ep.content_tier = content_tier
                                existing_ep.genre = genre
                                existing_ep.region = region
                                existing_ep.is_vertical = is_vertical
                                existing_ep.thumbnail = thumbnail
                                existing_ep.description = description
                                existing_ep.updated_at = datetime.now(timezone.utc)
                                episodes_to_index.append(existing_ep)
                        else:
                            report["episodes"]["unchanged"] += 1
                    else:
                        report["episodes"]["inserted"] += 1
                        new_ep = Episode(
                            id=ep_id,
                            program_id=prog_fk,
                            raw_program_id=raw_prog_id,
                            title=title,
                            slug=slug,
                            description=description,
                            episode_number=parse_int(row.get("episode_number")),
                            duration=duration_str,
                            duration_seconds=duration_sec,
                            views=views,
                            is_enable=is_enable,
                            is_free=is_free,
                            published_date=parse_datetime(row.get("published_date")),
                            release_dt=parse_datetime(row.get("release_dt")),
                            expiry_dt=parse_datetime(row.get("expiry_dt")),
                            ad_tag_url_android=clean_str(row.get("ad_tag_url_android")),
                            ad_tag_url_ios=clean_str(row.get("ad_tag_url_ios")),
                            channel_name=clean_str(row.get("channel_name")),
                            channel_status=channel_status,
                            content_rating=clean_str(row.get("content_rating")),
                            content_tier=content_tier,
                            content_type=clean_str(row.get("content_type")),
                            genre=genre,
                            hashtags=clean_str(row.get("hashtags")),
                            insert_date=parse_datetime(row.get("insert_date")),
                            is_corrupt=parse_bool(row.get("is_corrupt"), default=False) if clean_str(row.get("is_corrupt")) else None,
                            is_latest=parse_bool(row.get("is_latest"), default=False) if clean_str(row.get("is_latest")) else None,
                            is_migrate=parse_bool(row.get("is_migrate"), default=False) if clean_str(row.get("is_migrate")) else None,
                            is_transcoded=parse_bool(row.get("is_transcoded"), default=False) if clean_str(row.get("is_transcoded")) else None,
                            is_vertical=is_vertical,
                            is_zong_migrated=parse_bool(row.get("is_zong_migrated"), default=False) if clean_str(row.get("is_zong_migrated")) else None,
                            keywords=clean_str(row.get("keywords")),
                            manual_description=clean_str(row.get("manual_description")),
                            meta_desc=clean_str(row.get("meta_desc")),
                            meta_keywords=clean_str(row.get("meta_keywords")),
                            meta_title=clean_str(row.get("meta_title")),
                            path=clean_str(row.get("path")),
                            popularity_rating=parse_float(row.get("popularity_rating")),
                            region=region,
                            source=clean_str(row.get("source")),
                            sourcerecord=clean_str(row.get("sourcerecord")),
                            thumbnail=thumbnail,
                            topic=clean_str(row.get("topic")),
                            video_id=clean_str(row.get("video_id")),
                            source_file=episodes_filename,
                            imported_at=datetime.now(timezone.utc),
                        )
                        existing_episodes[ep_id] = new_ep
                        if not dry_run:
                            self.db.add(new_ep)
                            episodes_to_index.append(new_ep)

            # -------------------------------------------------------------
            # STEP 3: Handle Dry-Run vs Commit
            # -------------------------------------------------------------
            if dry_run:
                self.db.rollback()
                report["status"] = "dry_run_completed"
                report["records_created"] = report["programs"]["inserted"] + report["episodes"]["inserted"]
                report["records_updated"] = report["programs"]["updated"] + report["episodes"]["updated"]
                report["total_records_processed"] = report["programs"]["rows_read"] + report["episodes"]["rows_read"]
                logger.info(
                    f"Dry run complete: Programs (ins={report['programs']['inserted']}, upd={report['programs']['updated']}, unch={report['programs']['unchanged']}), "
                    f"Episodes (ins={report['episodes']['inserted']}, upd={report['episodes']['updated']}, unch={report['episodes']['unchanged']})"
                )
                return report

            # Real commit to database
            self.db.commit()
            logger.info("Canonical database changes committed successfully.")

            # -------------------------------------------------------------
            # STEP 4: Synchronize to Meilisearch
            # -------------------------------------------------------------
            if self.client:
                try:
                    setup_tasks = setup_media_indexes(self.client)
                    wait_for_meili_tasks(self.client, setup_tasks, timeout_sec=20.0)

                    # Send all programs and episodes if initial import, or modified ones
                    all_programs = list(existing_programs.values()) if not programs_to_index else programs_to_index
                    all_episodes = list(existing_episodes.values()) if not episodes_to_index else episodes_to_index

                    prog_tasks = sync_programs_to_index(self.client, all_programs, batch_size=batch_size)
                    ep_tasks = sync_episodes_to_index(self.client, all_episodes, existing_programs, batch_size=batch_size)

                    submitted_tasks = prog_tasks + ep_tasks
                    report["meilisearch"]["submitted_tasks"] = submitted_tasks
                    job.meili_task_ids = submitted_tasks

                    task_report = wait_for_meili_tasks(self.client, submitted_tasks, timeout_sec=60.0)
                    if task_report["all_succeeded"]:
                        report["meilisearch"]["task_status"] = "succeeded"
                        report["meilisearch"]["indexed_documents"] = len(all_programs) + len(all_episodes)
                    else:
                        report["meilisearch"]["task_status"] = "partial_or_pending"
                        report["meilisearch"]["task_report"] = task_report
                except Exception as meili_err:
                    logger.error(f"Meilisearch synchronization error: {meili_err}")
                    report["meilisearch"]["task_status"] = "failed"
                    report["meilisearch"]["error"] = str(meili_err)

            # Update job record
            completed_time = datetime.now(timezone.utc)
            job.status = "completed" if report["meilisearch"]["task_status"] != "failed" else "search_sync_failed"
            job.records_processed = report["programs"]["rows_read"] + report["episodes"]["rows_read"]
            job.records_created = report["programs"]["inserted"] + report["episodes"]["inserted"]
            job.records_updated = report["programs"]["updated"] + report["episodes"]["updated"]
            job.records_failed = report["programs"]["rejected"] + report["episodes"]["rejected"]
            job.errors = report["errors"] + report["programs"]["invalid_samples"] + report["episodes"]["invalid_samples"]
            job.completed_at = completed_time

            self.db.commit()

            report["status"] = job.status
            report["completed_at"] = completed_time.isoformat()
            report["records_created"] = report["programs"]["inserted"] + report["episodes"]["inserted"]
            report["records_updated"] = report["programs"]["updated"] + report["episodes"]["updated"]
            report["total_records_processed"] = report["programs"]["rows_read"] + report["episodes"]["rows_read"]
            return report

        except Exception as e:
            self.db.rollback()
            logger.error(f"Fatal error during CSV import: {e}", exc_info=True)
            report["status"] = "failed"
            report["errors"].append(str(e))
            if not dry_run:
                try:
                    job.status = "failed"
                    job.errors.append({"fatal_error": str(e)})
                    job.completed_at = datetime.now(timezone.utc)
                    self.db.commit()
                except Exception:
                    pass
            raise


# Alias for compatibility
CSVImporter = CsvMediaImporter


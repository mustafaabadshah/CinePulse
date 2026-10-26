"""Administrative endpoints requiring API key authentication."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.core.security import verify_admin_key
from app.ingestion.importer import IngestionPipeline
from app.models import (
    Episode,
    ImportJob,
    Institution,
    Program,
    Publication,
    Researcher,
    SearchAnalyticsEvent,
)
from app.schemas.analytics import SearchAnalyticsRead, SearchAnalyticsSummary
from app.schemas.import_job import ImportJobRead
from app.search.client import get_meili_client
from app.search.indexes import (
    ALL_INDEXES,
    INDEX_EPISODES,
    INDEX_INSTITUTIONS,
    INDEX_PROGRAMS,
    INDEX_PUBLICATIONS,
    INDEX_RESEARCHERS,
    initialize_indexes,
)
from app.services.csv_importer import CsvMediaImporter
from app.services.meilisearch_indexer import (
    sync_episodes_to_index,
    sync_programs_to_index,
    wait_for_meili_tasks,
)

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(verify_admin_key)])


@router.get("/source-files")
def get_source_files_status() -> Dict[str, Any]:
    """Returns filesystem status and metadata for configured CSV source files."""
    data_dir = os.path.abspath(settings.csv_data_dir)
    files = {
        "enrichment_file": settings.csv_enrichment_file,
        "episodes_file": settings.csv_episodes_file,
    }

    result = {
        "data_dir": data_dir,
        "files": {},
    }

    for key, filename in files.items():
        fpath = os.path.join(data_dir, filename)
        exists = os.path.exists(fpath) and os.path.isfile(fpath)
        file_info: Dict[str, Any] = {
            "filename": filename,
            "path": fpath,
            "exists": exists,
            "readable": False,
            "size_bytes": 0,
            "modified_at": None,
        }
        if exists:
            try:
                stat = os.stat(fpath)
                file_info["size_bytes"] = stat.st_size
                file_info["modified_at"] = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                with open(fpath, "rb") as test_f:
                    test_f.read(100)
                file_info["readable"] = True
            except Exception as e:
                file_info["error"] = str(e)
        result["files"][key] = file_info

    return result


@router.post("/import", response_model=ImportJobRead)
def trigger_import(
    payload: Dict[str, Any] = Body(default_factory=dict),
    source_name: str = Query(default="csv"),
    source_type: str = Query(default="csv", description="'csv' for prod CSV files or 'fixtures' for synthetic JSON"),
    dry_run: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> ImportJobRead:
    """Imports CSV media catalog records or research fixtures, persists to relational DB, and indexes into Meilisearch."""
    client = get_meili_client()

    # If source_type is CSV or no payload provided and CSV files exist
    if source_type == "csv" or not payload or source_name == "csv":
        importer = CsvMediaImporter(db=db, client=client)
        report = importer.run_import(
            data_dir=settings.csv_data_dir,
            dry_run=dry_run,
            enrichment_filename=settings.csv_enrichment_file,
            episodes_filename=settings.csv_episodes_file,
        )

        # Build ImportJobRead representation
        total_read = report["programs"]["rows_read"] + report["episodes"]["rows_read"]
        total_created = report["programs"]["inserted"] + report["episodes"]["inserted"]
        total_updated = report["programs"]["updated"] + report["episodes"]["updated"]
        total_failed = report["programs"]["rejected"] + report["episodes"]["rejected"]

        status = "completed" if not dry_run else "dry_run_completed"
        if report.get("status") == "failed":
            status = "failed"

        # Combine error samples and structured report
        err_list = report.get("errors", []) + report["programs"]["invalid_samples"] + report["episodes"]["invalid_samples"]
        # Include detailed breakdown inside errors metadata block
        err_list.append({"import_report": report})

        job_read = ImportJobRead(
            id=report["job_id"],
            status=status,
            source_name=f"{settings.csv_enrichment_file} + {settings.csv_episodes_file}",
            dry_run=dry_run,
            records_processed=total_read,
            records_created=total_created,
            records_updated=total_updated,
            records_failed=total_failed,
            errors=err_list,
            meili_task_ids=report.get("meilisearch", {}).get("submitted_tasks", []),
            started_at=datetime.fromisoformat(report["started_at"]),
            completed_at=datetime.fromisoformat(report["completed_at"]) if "completed_at" in report else datetime.now(timezone.utc),
        )
        return job_read

    # Handle fixture import fallback
    pipeline = IngestionPipeline(db, client=client)
    if not payload or not any(k in payload for k in ["institutions", "researchers", "publications"]):
        fixture_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "fixtures",
                "synthetic_research_data.json",
            )
        )
        if os.path.exists(fixture_path):
            with open(fixture_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            source_name = "default_synthetic_fixture"
        else:
            raise HTTPException(status_code=400, detail="Empty payload and default fixture file not found.")

    job = pipeline.run_import(data=payload, source_name=source_name, dry_run=dry_run)
    return ImportJobRead.model_validate(job)


@router.get("/imports", response_model=List[ImportJobRead])
def list_import_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> List[ImportJobRead]:
    """Lists recent ingestion jobs."""
    jobs = (
        db.query(ImportJob).order_by(ImportJob.started_at.desc()).offset(offset).limit(limit).all()
    )
    return [ImportJobRead.model_validate(j) for j in jobs]


@router.get("/imports/{job_id}", response_model=ImportJobRead)
def get_import_job(job_id: str, db: Session = Depends(get_db)) -> ImportJobRead:
    """Retrieves status and error details for a specific ingestion job."""
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Import job '{job_id}' not found.")
    return ImportJobRead.model_validate(job)


@router.get("/index-status")
def get_index_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns index names, database counts, indexed counts, pending/failed task counts, and last synchronization time."""
    client = get_meili_client()

    counts_db = {
        "episodes": db.query(Episode).count(),
        "programs": db.query(Program).count(),
        "researchers": db.query(Researcher).count(),
        "publications": db.query(Publication).count(),
        "institutions": db.query(Institution).count(),
    }

    counts_meili = {}
    meili_reachable = False
    pending_tasks = 0
    failed_tasks = 0

    try:
        health = client.health()
        meili_reachable = health.get("status") == "available"

        for idx_name in ALL_INDEXES:
            try:
                stats = client.index(idx_name).get_stats()
                counts_meili[idx_name] = stats.number_of_documents
            except Exception:
                counts_meili[idx_name] = 0

        # Query recent tasks
        recent_tasks = client.get_tasks({"limit": 20})
        task_list = recent_tasks.get("results") if isinstance(recent_tasks, dict) else getattr(recent_tasks, "results", [])
        for t in task_list:
            status = getattr(t, "status", None) or (t.get("status") if isinstance(t, dict) else None)
            if status in ("enqueued", "processing"):
                pending_tasks += 1
            elif status == "failed":
                failed_tasks += 1

    except Exception as e:
        logger.warning(f"Error checking Meilisearch index status: {e}")

    # Check last completed import job
    last_job = (
        db.query(ImportJob)
        .filter(ImportJob.status.in_(["completed", "running"]))
        .order_by(ImportJob.started_at.desc())
        .first()
    )

    last_sync_time = last_job.completed_at.isoformat() if last_job and last_job.completed_at else (last_job.started_at.isoformat() if last_job else None)

    return {
        "status": "healthy" if meili_reachable else "degraded",
        "meilisearch_reachable": meili_reachable,
        "indexes": {
            name: {
                "database_count": counts_db.get(name, 0),
                "indexed_count": counts_meili.get(name, 0),
                "is_synchronized": counts_db.get(name, 0) == counts_meili.get(name, 0),
            }
            for name in ALL_INDEXES
        },
        "pending_tasks_count": pending_tasks,
        "failed_tasks_count": failed_tasks,
        "last_sync_time": last_sync_time,
    }


@router.post("/reindex")
def trigger_reindex(db: Session = Depends(get_db)):
    """Reindexes all canonical relational database records into Meilisearch from scratch."""
    client = get_meili_client()
    logger.info("Admin initiated full reindex.")

    # 1. Initialize / reset settings
    initialize_indexes(client)

    # 2. Build institution docs
    institutions = db.query(Institution).all()
    inst_name_map = {i.id: i.name for i in institutions}
    inst_docs = [
        {
            "id": i.id,
            "name": i.name,
            "country": i.country,
            "city": i.city,
            "website_url": i.website_url,
            "ror_id": i.ror_id,
        }
        for i in institutions
    ]

    # 3. Build researcher docs
    researchers = db.query(Researcher).all()
    res_docs = [
        {
            "id": r.id,
            "full_name": r.full_name,
            "institution_id": r.institution_id,
            "institution_name": inst_name_map.get(r.institution_id, "Unknown Institution"),
            "department": r.department,
            "country": r.country,
            "research_interests": r.research_interests,
            "biography": r.biography,
            "contact_email_verified": r.contact_email_verified,
            "contact_email": r.contact_email,
            "contact_source_url": r.contact_source_url,
            "official_profile_url": r.official_profile_url,
            "is_synthetic": r.is_synthetic,
        }
        for r in researchers
    ]

    # 4. Build publication docs
    publications = db.query(Publication).all()
    pub_docs = [
        {
            "id": p.id,
            "title": p.title,
            "abstract": p.abstract,
            "authors": p.authors,
            "primary_institution_id": p.primary_institution_id,
            "institution_name": inst_name_map.get(p.primary_institution_id, "")
            if p.primary_institution_id
            else None,
            "publication_year": p.publication_year,
            "venue": p.venue,
            "doi": p.doi,
            "canonical_url": p.canonical_url,
            "keywords": p.keywords,
            "source_provider": p.source_provider,
            "is_synthetic": p.is_synthetic,
        }
        for p in publications
    ]

    # 5. Media catalog docs (programs & episodes)
    programs = db.query(Program).all()
    programs_map = {p.id: p for p in programs}
    episodes = db.query(Episode).all()

    task_ids = []
    if inst_docs:
        t = client.index(INDEX_INSTITUTIONS).add_documents(inst_docs, primary_key="id")
        task_ids.append(t.task_uid)

    if res_docs:
        t = client.index(INDEX_RESEARCHERS).add_documents(res_docs, primary_key="id")
        task_ids.append(t.task_uid)

    if pub_docs:
        t = client.index(INDEX_PUBLICATIONS).add_documents(pub_docs, primary_key="id")
        task_ids.append(t.task_uid)

    if programs:
        prog_tasks = sync_programs_to_index(client, programs)
        task_ids.extend(prog_tasks)

    if episodes:
        ep_tasks = sync_episodes_to_index(client, episodes, programs_map)
        task_ids.extend(ep_tasks)

    # Wait for completion of indexing tasks
    report = wait_for_meili_tasks(client, task_ids, timeout_sec=60.0)

    return {
        "status": "completed" if report["all_succeeded"] else "partial",
        "reindexed_counts": {
            "institutions": len(inst_docs),
            "researchers": len(res_docs),
            "publications": len(pub_docs),
            "programs": len(programs),
            "episodes": len(episodes),
        },
        "task_report": report,
    }


@router.get("/search-analytics", response_model=SearchAnalyticsSummary)
def get_search_analytics(
    limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)
) -> SearchAnalyticsSummary:
    """Returns aggregated search analytics: total queries, zero-result rate, and latency metrics."""
    total_searches = db.query(func.count(SearchAnalyticsEvent.id)).scalar() or 0
    zero_searches = (
        db.query(func.count(SearchAnalyticsEvent.id))
        .filter(SearchAnalyticsEvent.zero_result.is_(True))
        .scalar()
        or 0
    )
    zero_result_rate = (
        round((zero_searches / total_searches * 100), 2) if total_searches > 0 else 0.0
    )

    avg_latency = db.query(func.avg(SearchAnalyticsEvent.latency_ms)).scalar() or 0.0

    # Calculate approx 95th percentile latency from recent records
    recent_events = (
        db.query(SearchAnalyticsEvent)
        .order_by(SearchAnalyticsEvent.timestamp.desc())
        .limit(100)
        .all()
    )
    latencies = sorted([e.latency_ms for e in recent_events])
    p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else round(avg_latency, 2)

    # Top queries
    top_query_records = (
        db.query(
            SearchAnalyticsEvent.query_text, func.count(SearchAnalyticsEvent.id).label("count")
        )
        .filter(SearchAnalyticsEvent.query_text != "*")
        .group_by(SearchAnalyticsEvent.query_text)
        .order_by(func.count(SearchAnalyticsEvent.id).desc())
        .limit(10)
        .all()
    )
    top_queries = [{"query": r[0], "count": r[1]} for r in top_query_records]

    recent_reads = [SearchAnalyticsRead.model_validate(e) for e in recent_events[:limit]]

    return SearchAnalyticsSummary(
        total_searches=total_searches,
        zero_result_searches=zero_searches,
        zero_result_rate=zero_result_rate,
        average_latency_ms=round(avg_latency, 2),
        p95_latency_ms=round(p95_latency, 2),
        top_queries=top_queries,
        recent_searches=recent_reads,
    )

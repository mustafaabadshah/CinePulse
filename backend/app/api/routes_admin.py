"""Administrative endpoints requiring API key authentication."""

import json
from typing import Any, Dict, List

from app.core.database import get_db
from app.core.logging import logger
from app.core.security import verify_admin_key
from app.ingestion.importer import IngestionPipeline
from app.models import ImportJob, Institution, Publication, Researcher, SearchAnalyticsEvent
from app.schemas.analytics import SearchAnalyticsRead, SearchAnalyticsSummary
from app.schemas.import_job import ImportJobRead
from app.search.client import get_meili_client
from app.search.indexes import (
    INDEX_INSTITUTIONS,
    INDEX_PUBLICATIONS,
    INDEX_RESEARCHERS,
    initialize_indexes,
)
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(verify_admin_key)])


@router.post("/import", response_model=ImportJobRead)
def trigger_import(
    payload: Dict[str, Any] = Body(default_factory=dict),
    source_name: str = Query(default="admin_upload"),
    dry_run: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> ImportJobRead:
    """Imports research records, validates schema, persists to relational DB, and indexes into Meilisearch."""
    pipeline = IngestionPipeline(db)
    # If no payload passed in body, try to load default fixture
    if not payload or not any(
        k in payload for k in ["institutions", "researchers", "publications"]
    ):
        import os

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
            raise HTTPException(
                status_code=400, detail="Empty payload and default fixture file not found."
            )

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

    task_ids = []
    if inst_docs:
        t = client.index(INDEX_INSTITUTIONS).add_documents(inst_docs, primary_key="id")
        task_ids.append({"index": INDEX_INSTITUTIONS, "task_uid": t.task_uid})

    if res_docs:
        t = client.index(INDEX_RESEARCHERS).add_documents(res_docs, primary_key="id")
        task_ids.append({"index": INDEX_RESEARCHERS, "task_uid": t.task_uid})

    if pub_docs:
        t = client.index(INDEX_PUBLICATIONS).add_documents(pub_docs, primary_key="id")
        task_ids.append({"index": INDEX_PUBLICATIONS, "task_uid": t.task_uid})

    # Wait for completion of indexing tasks
    status_reports = []
    for t_info in task_ids:
        finished = client.wait_for_task(t_info["task_uid"], timeout_in_ms=10000)
        status_reports.append(
            {
                "index": t_info["index"],
                "task_uid": t_info["task_uid"],
                "status": finished.status,
            }
        )

    return {
        "status": "completed",
        "reindexed_counts": {
            "institutions": len(inst_docs),
            "researchers": len(res_docs),
            "publications": len(pub_docs),
        },
        "tasks": status_reports,
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

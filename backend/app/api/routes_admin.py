"""Administrative endpoints for Tamasha media catalog management."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.core.security import verify_admin_key
from app.models import Episode, ImportJob, MediaArtwork, Program
from app.schemas.import_job import ImportJobRead
from app.search.client import get_meili_client
from app.services.data_normalizer import normalize_thumbnail_url
from app.search.indexes import (
    ALL_INDEXES,
    INDEX_EPISODES,
    INDEX_PROGRAMS,
    initialize_indexes,
)
from app.services.csv_importer import CsvMediaImporter
from app.services.meilisearch_indexer import (
    rebuild_media_indexes_from_db,
    sync_episodes_to_index,
    sync_programs_to_index,
    wait_for_meili_tasks,
)

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(verify_admin_key)])


@router.get("/source-files")
def get_source_files_status() -> Dict[str, Any]:
    """Inspects the configured CSV data files on disk without changing database or search indexes."""
    data_dir = settings.csv_data_dir
    enrichment_path = os.path.abspath(os.path.join(data_dir, settings.csv_enrichment_file))
    episodes_path = os.path.abspath(os.path.join(data_dir, settings.csv_episodes_file))

    def _file_info(path: str, filename: str) -> Dict[str, Any]:
        exists = os.path.exists(path) and os.path.isfile(path)
        info: Dict[str, Any] = {
            "filename": filename,
            "path": path,
            "exists": exists,
            "size_bytes": os.path.getsize(path) if exists else 0,
            "modified_at": datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).isoformat()
            if exists
            else None,
        }
        if exists:
            try:
                with open(path, "rb") as f:
                    header = f.read(4)
                    info["has_bom"] = header.startswith(b"\xef\xbb\xbf")
                # Count lines without loading entire file in memory
                with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
                    lines = sum(1 for _ in f)
                    info["total_rows"] = max(0, lines - 1)
            except Exception as e:
                info["read_error"] = str(e)
        return info

    return {
        "data_dir": data_dir,
        "files": {
            "enrichment_file": _file_info(enrichment_path, settings.csv_enrichment_file),
            "episodes_file": _file_info(episodes_path, settings.csv_episodes_file),
        },
    }


@router.post("/import", response_model=ImportJobRead)
def trigger_import(
    dry_run: bool = Query(default=False, description="Run validation without persisting changes"),
    db: Session = Depends(get_db),
) -> ImportJobRead:
    """Triggers transactional ingestion of prod_enrichment.csv and episodes_prod.csv."""
    client = get_meili_client()
    importer = CsvMediaImporter(db=db, client=client)
    report = importer.run_import(
        data_dir=settings.csv_data_dir,
        dry_run=dry_run,
        enrichment_filename=settings.csv_enrichment_file,
        episodes_filename=settings.csv_episodes_file,
    )

    total_read = report["programs"]["rows_read"] + report["episodes"]["rows_read"]
    total_created = report["programs"]["inserted"] + report["episodes"]["inserted"]
    total_updated = report["programs"]["updated"] + report["episodes"]["updated"]
    total_failed = report["programs"]["rejected"] + report["episodes"]["rejected"]

    status = "completed" if not dry_run else "dry_run_completed"
    if report.get("status") == "failed":
        status = "failed"

    err_list = report.get("errors", []) + report["programs"]["invalid_samples"] + report["episodes"]["invalid_samples"]
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


@router.get("/imports", response_model=List[ImportJobRead])
def list_import_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> List[ImportJobRead]:
    """Lists recent media catalog ingestion jobs."""
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
    """Returns media index names, database counts, indexed counts, pending/failed tasks, and synchronization status."""
    client = get_meili_client()

    counts_db = {
        "episodes": db.query(Episode).count(),
        "programs": db.query(Program).count(),
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
            t_status = getattr(t, "status", None) or (t.get("status") if isinstance(t, dict) else None)
            if t_status in ("enqueued", "processing"):
                pending_tasks += 1
            elif t_status == "failed":
                failed_tasks += 1
    except Exception as e:
        logger.warning(f"Error checking Meilisearch index status: {e}")

    last_job = db.query(ImportJob).filter(ImportJob.dry_run.is_(False)).order_by(ImportJob.started_at.desc()).first()

    return {
        "healthy": meili_reachable,
        "indexes": {
            INDEX_EPISODES: {
                "database_count": counts_db["episodes"],
                "indexed_count": counts_meili.get(INDEX_EPISODES, 0),
                "is_consistent": counts_db["episodes"] == counts_meili.get(INDEX_EPISODES, 0),
            },
            INDEX_PROGRAMS: {
                "database_count": counts_db["programs"],
                "indexed_count": counts_meili.get(INDEX_PROGRAMS, 0),
                "is_consistent": counts_db["programs"] == counts_meili.get(INDEX_PROGRAMS, 0),
            },
        },
        "tasks": {
            "pending": pending_tasks,
            "failed": failed_tasks,
        },
        "last_sync_time": last_job.completed_at.isoformat() if last_job and last_job.completed_at else None,
        "last_job_status": last_job.status if last_job else None,
    }


@router.post("/reindex")
def trigger_reindex(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Rebuilds the media search indexes directly from the canonical database."""
    client = get_meili_client()
    return rebuild_media_indexes_from_db(db, client)


@router.get("/artwork")
def list_media_artwork(
    status: Optional[str] = Query(default=None),
    entity_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Lists media artwork entries for administrative review and audit."""
    q = db.query(MediaArtwork)
    if status:
        q = q.filter(MediaArtwork.verification_status == status)
    if entity_type:
        q = q.filter(MediaArtwork.entity_type == entity_type)

    total = q.count()
    items = q.order_by(MediaArtwork.id.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "id": a.id,
                "entity_id": a.entity_id,
                "entity_type": a.entity_type,
                "artwork_url": a.artwork_url,
                "artwork_source": a.artwork_source,
                "artwork_type": a.artwork_type,
                "verification_status": a.verification_status,
                "match_confidence": a.match_confidence,
                "failure_reason": a.failure_reason,
                "last_checked": a.last_checked.isoformat() if a.last_checked else None,
                "created_at": a.created_at.isoformat(),
            }
            for a in items
        ],
    }


@router.post("/artwork/approve")
def approve_media_artwork(payload: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Approves a candidate artwork match and marks it verified."""
    artwork_id = payload.get("id")
    if not artwork_id:
        raise HTTPException(status_code=400, detail="Missing artwork 'id'.")

    art = db.query(MediaArtwork).filter(MediaArtwork.id == artwork_id).first()
    if not art:
        raise HTTPException(status_code=404, detail=f"Artwork record '{artwork_id}' not found.")

    art.verification_status = "verified"
    art.last_checked = datetime.now(timezone.utc)
    db.commit()

    return {"status": "approved", "id": art.id, "verification_status": art.verification_status}


@router.post("/artwork/reject")
def reject_media_artwork(payload: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Rejects an artwork match and records the reason."""
    artwork_id = payload.get("id")
    reason = payload.get("reason", "Rejected by administrator")
    if not artwork_id:
        raise HTTPException(status_code=400, detail="Missing artwork 'id'.")

    art = db.query(MediaArtwork).filter(MediaArtwork.id == artwork_id).first()
    if not art:
        raise HTTPException(status_code=404, detail=f"Artwork record '{artwork_id}' not found.")

    art.verification_status = "failed"
    art.failure_reason = reason
    art.last_checked = datetime.now(timezone.utc)
    db.commit()

    return {"status": "rejected", "id": art.id, "failure_reason": art.failure_reason}


@router.post("/artwork/sync-inherited")
def sync_inherited_artwork(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Scans all programs and seeds verified artwork from child episodes."""
    programs = db.query(Program).all()
    created_count = 0
    updated_count = 0

    for prog in programs:
        first_ep = (
            db.query(Episode)
            .filter(Episode.program_id == prog.id, Episode.thumbnail.isnot(None))
            .order_by(Episode.episode_number.asc().nulls_last(), Episode.views.desc())
            .first()
        )
        if first_ep and first_ep.thumbnail:
            norm_url = normalize_thumbnail_url(first_ep.thumbnail)
            existing = db.query(MediaArtwork).filter(
                MediaArtwork.entity_id == prog.id,
                MediaArtwork.entity_type == "program"
            ).first()

            if not existing:
                new_art = MediaArtwork(
                    entity_id=prog.id,
                    entity_type="program",
                    artwork_url=norm_url,
                    artwork_source="child_episode",
                    artwork_type="poster",
                    verification_status="verified",
                    match_confidence=1.0,
                    last_checked=datetime.now(timezone.utc),
                )
                db.add(new_art)
                created_count += 1
            else:
                existing.artwork_url = norm_url
                existing.verification_status = "verified"
                existing.last_checked = datetime.now(timezone.utc)
                updated_count += 1

    db.commit()
    return {
        "status": "completed",
        "total_programs": len(programs),
        "created_records": created_count,
        "updated_records": updated_count,
    }

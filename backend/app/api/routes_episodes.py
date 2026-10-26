"""Episode retrieval endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Integer, cast
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.episode import Episode
from app.models.program import Program
from app.services.data_normalizer import normalize_thumbnail_url, split_tags

router = APIRouter(prefix="/episodes", tags=["Episodes"])


@router.get("")
def list_episodes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    program_id: Optional[str] = Query(default=None),
    is_free: Optional[bool] = Query(default=None),
    content_tier: Optional[str] = Query(default=None),
    genre: Optional[str] = Query(default=None),
    sort: Optional[str] = Query(default=None, description="Sort order: 'sequence', 'views', 'duration_asc', 'duration_desc'"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieves paginated episodes with optional filters."""
    query = db.query(Episode)
    if program_id:
        query = query.filter((Episode.program_id == program_id) | (Episode.raw_program_id == program_id))
    if is_free is not None:
        query = query.filter(Episode.is_free == is_free)
    if content_tier:
        query = query.filter(Episode.content_tier == content_tier)
    if genre:
        query = query.filter(Episode.genre.ilike(f"%{genre}%"))

    total = query.count()

    # Determine ordering: default to chronological sequence when querying a program's episodes
    if sort == "sequence" or (sort is None and program_id):
        query = query.order_by(
            Episode.episode_number.asc().nulls_last(),
            cast(Episode.id, Integer).asc()
        )
    elif sort == "duration_asc":
        query = query.order_by(Episode.duration_seconds.asc().nulls_last())
    elif sort == "duration_desc":
        query = query.order_by(Episode.duration_seconds.desc().nulls_last())
    else:
        query = query.order_by(Episode.views.desc())

    items = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "id": ep.id,
                "title": ep.title,
                "slug": ep.slug,
                "episode_number": ep.episode_number,
                "program_id": ep.program_id or ep.raw_program_id,
                "duration": ep.duration,
                "duration_seconds": ep.duration_seconds,
                "views": ep.views,
                "is_free": ep.is_free,
                "content_tier": ep.content_tier,
                "genre": ep.genre,
                "genre_list": split_tags(ep.genre),
                "thumbnail": normalize_thumbnail_url(ep.thumbnail),
                "region": ep.region,
                "is_vertical": ep.is_vertical,
            }
            for ep in items
        ],
    }


@router.get("/{id}")
def get_episode(id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves full details for an episode including its parent program and sibling episodes."""
    ep = db.query(Episode).filter(Episode.id == id).first()
    if not ep:
        raise HTTPException(status_code=404, detail=f"Episode '{id}' not found.")

    program = None
    if ep.program_id:
        program = db.query(Program).filter(Program.id == ep.program_id).first()

    # Query sibling episodes from the same program in sequence
    sibling_episodes = []
    if ep.program_id:
        siblings = []
        if ep.episode_number is not None:
            siblings = (
                db.query(Episode)
                .filter(Episode.program_id == ep.program_id, Episode.episode_number > ep.episode_number)
                .order_by(Episode.episode_number.asc())
                .limit(6)
                .all()
            )
        if not siblings:
            siblings = (
                db.query(Episode)
                .filter(Episode.program_id == ep.program_id, Episode.id != ep.id)
                .order_by(Episode.episode_number.asc().nulls_last(), cast(Episode.id, Integer).asc())
                .limit(6)
                .all()
            )

        sibling_episodes = [
            {
                "id": s.id,
                "title": s.title,
                "episode_number": s.episode_number,
                "duration": s.duration,
                "duration_seconds": s.duration_seconds,
                "views": s.views,
                "thumbnail": normalize_thumbnail_url(s.thumbnail),
                "is_free": s.is_free,
            }
            for s in siblings
        ]

    return {
        "id": ep.id,
        "title": ep.title,
        "slug": ep.slug,
        "description": ep.description,
        "program_id": ep.program_id or ep.raw_program_id,
        "duration": ep.duration,
        "duration_seconds": ep.duration_seconds,
        "views": ep.views,
        "is_free": ep.is_free,
        "is_enable": ep.is_enable,
        "content_tier": ep.content_tier,
        "genre": ep.genre,
        "genre_list": split_tags(ep.genre),
        "region": ep.region,
        "is_vertical": ep.is_vertical,
        "thumbnail": normalize_thumbnail_url(ep.thumbnail),
        "channel_name": ep.channel_name or (program.channel_name if program else None),
        "channel_status": ep.channel_status,
        "source_file": ep.source_file,
        "imported_at": ep.imported_at.isoformat() if ep.imported_at else None,
        "created_at": ep.created_at.isoformat(),
        "updated_at": ep.updated_at.isoformat(),
        "program": {
            "id": program.id,
            "type": program.type,
            "name": program.name,
            "slug": program.slug,
            "channel_name": program.channel_name,
            "info_language": program.info_language,
            "info_genre": program.info_genre,
            "info_content_type": program.info_content_type,
            "info_staring": program.info_staring,
            "starring_list": split_tags(program.info_staring),
        }
        if program
        else None,
        "sibling_episodes": sibling_episodes,
    }

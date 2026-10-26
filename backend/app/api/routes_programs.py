"""Program and Channel retrieval endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.episode import Episode
from app.models.program import Program
from app.services.data_normalizer import split_tags

router = APIRouter(prefix="/programs", tags=["Programs"])


@router.get("")
def list_programs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    type: Optional[str] = Query(default=None),
    channel_name: Optional[str] = Query(default=None),
    info_language: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieves paginated programs with optional filters."""
    query = db.query(Program)
    if type:
        query = query.filter(Program.type == type)
    if channel_name:
        query = query.filter(Program.channel_name == channel_name)
    if info_language:
        query = query.filter(Program.info_language == info_language)

    total = query.count()
    items = query.order_by(Program.name.asc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "id": p.id,
                "type": p.type,
                "name": p.name,
                "slug": p.slug,
                "channel_name": p.channel_name,
                "info_language": p.info_language,
                "info_genre": p.info_genre,
                "genre_list": split_tags(p.info_genre),
                "info_content_type": p.info_content_type,
                "info_staring": p.info_staring,
                "starring_list": split_tags(p.info_staring),
            }
            for p in items
        ],
    }


@router.get("/{id}")
def get_program(id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves full details for a program including its child episodes."""
    p = db.query(Program).filter(Program.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Program '{id}' not found.")

    episodes = (
        db.query(Episode)
        .filter(Episode.program_id == id)
        .order_by(Episode.views.desc())
        .limit(20)
        .all()
    )

    episode_count = db.query(Episode).filter(Episode.program_id == id).count()

    return {
        "id": p.id,
        "type": p.type,
        "name": p.name,
        "slug": p.slug,
        "channel_name": p.channel_name,
        "info_language": p.info_language,
        "info_genre": p.info_genre,
        "genre_list": split_tags(p.info_genre),
        "info_meta_keywords": p.info_meta_keywords,
        "info_content_type": p.info_content_type,
        "info_staring": p.info_staring,
        "starring_list": split_tags(p.info_staring),
        "source_file": p.source_file,
        "imported_at": p.imported_at.isoformat() if p.imported_at else None,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
        "episode_count": episode_count,
        "episodes": [
            {
                "id": ep.id,
                "title": ep.title,
                "slug": ep.slug,
                "duration": ep.duration,
                "duration_seconds": ep.duration_seconds,
                "views": ep.views,
                "is_free": ep.is_free,
                "content_tier": ep.content_tier,
                "thumbnail": ep.thumbnail,
                "genre": ep.genre,
            }
            for ep in episodes
        ],
    }

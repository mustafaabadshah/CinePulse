"""Program and Channel retrieval endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Integer, cast
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.episode import Episode
from app.models.program import Program
from app.services.data_normalizer import normalize_thumbnail_url, split_tags

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
def get_program(
    id: str,
    sort: str = Query(default="sequence", description="Sort order: sequence or views"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieves full details for a program including its child episodes in sequence."""
    p = db.query(Program).filter(Program.id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Program '{id}' not found.")

    ep_query = db.query(Episode).filter(Episode.program_id == id)
    if sort == "views":
        ep_query = ep_query.order_by(Episode.views.desc())
    else:
        # Default: chronological sequence by episode_number, then sequential ID
        ep_query = ep_query.order_by(
            Episode.episode_number.asc().nulls_last(),
            cast(Episode.id, Integer).asc()
        )

    episodes = ep_query.limit(limit).all()
    episode_count = db.query(Episode).filter(Episode.program_id == id).count()

    primary_thumb = None
    if episodes and episodes[0].thumbnail:
        primary_thumb = normalize_thumbnail_url(episodes[0].thumbnail)

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
        "thumbnail": primary_thumb,
        "episode_count": episode_count,
        "episodes": [
            {
                "id": ep.id,
                "title": ep.title,
                "slug": ep.slug,
                "episode_number": ep.episode_number,
                "duration": ep.duration,
                "duration_seconds": ep.duration_seconds,
                "views": ep.views,
                "is_free": ep.is_free,
                "content_tier": ep.content_tier,
                "thumbnail": normalize_thumbnail_url(ep.thumbnail),
                "genre": ep.genre,
            }
            for ep in episodes
        ],
    }

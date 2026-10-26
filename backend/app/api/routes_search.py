"""Search API endpoint with allowlisted filter extraction."""

from typing import Optional

from app.api.deps import get_search_service
from app.schemas.search import SearchRequest, SearchResponse
from app.search.service import SearchService
from fastapi import APIRouter, Depends, Query

router = APIRouter(tags=["Search"])


@router.get("/search", response_model=SearchResponse)
def execute_search(
    q: str = Query(default="", description="Search query string"),
    type: str = Query(
        default="all",
        description="Record type: 'all', 'researchers', 'publications', or 'institutions'",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Results per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    sort: Optional[str] = Query(default=None, description="Sort order e.g. publication_year:desc"),
    country: Optional[str] = Query(default=None, description="Country filter"),
    institution_name: Optional[str] = Query(default=None, description="Institution filter"),
    research_interests: Optional[str] = Query(default=None, description="Research interest filter"),
    publication_year: Optional[int] = Query(default=None, description="Publication year filter"),
    venue: Optional[str] = Query(default=None, description="Venue filter"),
    keywords: Optional[str] = Query(default=None, description="Keywords filter"),
    source_provider: Optional[str] = Query(default=None, description="Source provider filter"),
    is_synthetic: Optional[bool] = Query(default=None, description="Synthetic record filter"),
    contact_email_verified: Optional[bool] = Query(
        default=None, description="Verified contact filter"
    ),
    is_free: Optional[bool] = Query(default=None, description="Free episode filter"),
    content_tier: Optional[str] = Query(default=None, description="Content tier filter (avod, pro, jazz_flex)"),
    genre: Optional[str] = Query(default=None, description="Genre filter"),
    channel_name: Optional[str] = Query(default=None, description="Channel/Network filter"),
    info_language: Optional[str] = Query(default=None, description="Language filter"),
    info_content_type: Optional[str] = Query(default=None, description="Content format filter"),
    region: Optional[str] = Query(default=None, description="Distribution region filter"),
    is_vertical: Optional[str] = Query(default=None, description="Vertical video filter ('mini')"),
    program_id: Optional[str] = Query(default=None, description="Parent program filter"),
    search_service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """Executes a search query against Meilisearch with safe allowlisted filters."""
    filters = {}
    if country is not None:
        filters["country"] = country
    if institution_name is not None:
        filters["institution_name"] = institution_name
    if research_interests is not None:
        filters["research_interests"] = research_interests
    if publication_year is not None:
        filters["publication_year"] = publication_year
    if venue is not None:
        filters["venue"] = venue
    if keywords is not None:
        filters["keywords"] = keywords
    if source_provider is not None:
        filters["source_provider"] = source_provider
    if is_synthetic is not None:
        filters["is_synthetic"] = is_synthetic
    if contact_email_verified is not None:
        filters["contact_email_verified"] = contact_email_verified
    if is_free is not None:
        filters["is_free"] = is_free
    if content_tier is not None:
        filters["content_tier"] = content_tier
    if genre is not None:
        filters["genre"] = genre
    if channel_name is not None:
        filters["channel_name"] = channel_name
    if info_language is not None:
        filters["info_language"] = info_language
    if info_content_type is not None:
        filters["info_content_type"] = info_content_type
    if region is not None:
        filters["region"] = region
    if is_vertical is not None:
        filters["is_vertical"] = is_vertical
    if program_id is not None:
        filters["program_id"] = program_id

    req = SearchRequest(
        q=q,
        type=type,
        limit=limit,
        offset=offset,
        sort=sort,
        filters=filters if filters else None,
    )
    return search_service.search(req)

"""Pydantic schemas for Tamasha Media Search queries and responses."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    q: str = Field(default="", description="Search query string")
    type: str = Field(
        default="all",
        description="Catalog type: 'all', 'episodes', 'programs', or 'channels'",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Number of results per page")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    sort: Optional[str] = Field(default=None, description="Sort order, e.g. views:desc, duration_seconds:asc")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Allowlisted key-value filters"
    )
    facets: Optional[List[str]] = Field(
        default=None, description="Facets to compute distributions for"
    )
    disable_nlp: bool = Field(
        default=False, description="Explicitly bypass NLP entity extraction if True"
    )


class SearchResultItem(BaseModel):
    id: str
    type: str  # "episode" or "program"
    title: str  # episode title or program name
    subtitle: Optional[str] = None  # channel, duration, language
    snippet: Optional[str] = None  # description or starring cast
    tags: List[str] = Field(default_factory=list)  # genres, tags
    source_url: Optional[str] = None  # thumbnail url if available
    thumbnail: Optional[str] = None
    views: Optional[int] = None
    duration: Optional[str] = None
    duration_seconds: Optional[int] = None
    is_free: Optional[bool] = None
    content_tier: Optional[str] = None
    channel_name: Optional[str] = None
    program_name: Optional[str] = None
    content_type: Optional[str] = None
    raw: Dict[str, Any] = Field(default_factory=dict)
    formatted: Optional[Dict[str, Any]] = Field(default=None, description="Highlighted attributes")


class SearchResponse(BaseModel):
    query: str
    type: str
    total_hits: int
    offset: int
    limit: int
    page: int
    total_pages: int
    processing_time_ms: float
    hits: List[SearchResultItem]
    facet_distribution: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    nlp: Optional[Dict[str, Any]] = Field(
        default=None, description="Extracted NLP entities, inferred filters, and query interpretation"
    )


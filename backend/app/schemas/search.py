"""Pydantic schemas for Search queries and responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    q: str = Field(default="", description="Search query string")
    type: str = Field(
        default="all",
        description="Record type: 'all', 'researchers', 'publications', or 'institutions'",
    )
    limit: int = Field(default=20, ge=1, le=100, description="Number of results per page")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    sort: Optional[str] = Field(default=None, description="Sort order, e.g. publication_year:desc")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Allowlisted key-value filters"
    )
    facets: Optional[List[str]] = Field(
        default=None, description="Facets to compute distributions for"
    )


class SearchResultItem(BaseModel):
    id: str
    type: str  # "researcher", "publication", "institution"
    title: str  # full_name for researcher, title for publication, name for institution
    subtitle: Optional[str] = None  # institution, venue + year, country
    snippet: Optional[str] = None  # biography snippet, abstract snippet
    tags: List[str] = Field(default_factory=list)  # research_interests, keywords
    source_url: Optional[str] = None
    is_synthetic: bool = False
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

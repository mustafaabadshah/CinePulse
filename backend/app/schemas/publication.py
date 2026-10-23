"""Pydantic schemas for Publication."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PublicationBase(BaseModel):
    id: str = Field(..., description="Unique publication ID or DOI slug")
    title: str = Field(..., min_length=1, description="Paper title")
    abstract: Optional[str] = Field(None, description="Paper abstract")
    authors: List[str] = Field(default_factory=list, description="List of author names")
    primary_institution_id: Optional[str] = Field(
        None, description="Primary affiliated institution ID"
    )
    publication_year: int = Field(..., ge=1900, le=2100, description="Year of publication")
    venue: Optional[str] = Field(None, description="Conference, workshop, or journal name")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    canonical_url: Optional[str] = Field(None, description="Canonical publication or preprint URL")
    keywords: List[str] = Field(default_factory=list, description="Keywords and topic tags")
    source_provider: str = Field(
        default="synthetic", description="Originating provider (openalex, synthetic, etc.)"
    )
    is_synthetic: bool = Field(
        default=False, description="Flag indicating synthetic demonstration record"
    )


class PublicationCreate(PublicationBase):
    pass


class PublicationRead(PublicationBase):
    model_config = ConfigDict(from_attributes=True)

    imported_at: datetime
    created_at: datetime
    updated_at: datetime

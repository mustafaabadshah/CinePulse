"""Pydantic schemas for Researcher."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ResearcherBase(BaseModel):
    id: str = Field(..., description="Unique researcher ID, e.g. res_yann_lecun")
    full_name: str = Field(..., min_length=1, description="Full name of researcher")
    official_profile_url: Optional[str] = Field(
        None, description="Official university or lab profile"
    )
    institution_id: str = Field(..., description="Affiliated institution ID")
    department: Optional[str] = Field(None, description="Department or division")
    country: str = Field(..., min_length=1, description="Country of affiliated institution")
    research_interests: List[str] = Field(
        default_factory=list, description="List of technical domains and keywords"
    )
    biography: Optional[str] = Field(None, description="Researcher summary or bio")
    contact_email_verified: bool = Field(
        default=False, description="Whether email is authoritatively verified"
    )
    contact_email: Optional[str] = Field(None, description="Verified institutional public email")
    contact_source_url: Optional[str] = Field(
        None, description="URL source where contact was verified"
    )
    last_verified_at: Optional[datetime] = Field(
        None, description="Timestamp of contact verification"
    )
    is_synthetic: bool = Field(
        default=False, description="Flag indicating synthetic demonstration record"
    )


class ResearcherCreate(ResearcherBase):
    pass


class ResearcherRead(ResearcherBase):
    model_config = ConfigDict(from_attributes=True)

    institution_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

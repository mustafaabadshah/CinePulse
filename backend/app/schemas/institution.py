"""Pydantic schemas for Institution."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InstitutionBase(BaseModel):
    id: str = Field(..., description="Unique institution identifier, e.g. inst_mit")
    name: str = Field(..., min_length=1, description="Official institution name")
    country: str = Field(..., min_length=1, description="Country of institution")
    city: str = Field(..., min_length=1, description="City")
    website_url: Optional[str] = Field(None, description="Official URL")
    ror_id: Optional[str] = Field(None, description="Research Organization Registry ID")


class InstitutionCreate(InstitutionBase):
    pass


class InstitutionRead(InstitutionBase):
    model_config = ConfigDict(from_attributes=True)

    normalized_name: str
    created_at: datetime
    updated_at: datetime

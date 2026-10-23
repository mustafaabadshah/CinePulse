"""Pydantic schemas for Import Jobs."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ImportJobRequest(BaseModel):
    source_name: str = Field(
        default="fixture_file", description="Name or identifier of source file or provider"
    )
    dry_run: bool = Field(
        default=False,
        description="Whether to simulate ingestion without committing to DB or search",
    )


class ImportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    source_name: str
    dry_run: bool
    records_processed: int
    records_created: int
    records_updated: int
    records_failed: int
    errors: List[Dict[str, Any]]
    meili_task_ids: List[int]
    started_at: datetime
    completed_at: Optional[datetime]

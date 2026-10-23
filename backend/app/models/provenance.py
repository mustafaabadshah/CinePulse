"""Provenance and SourceRecord database model."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SourceRecord(Base):
    __tablename__ = "source_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # "researcher", "publication", "institution"
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_provider: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # "openalex", "synthetic", etc.
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_payload_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # SHA-256 hash for deduplication
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

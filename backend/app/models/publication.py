"""Publication database model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.institution import Institution


class Publication(Base, TimestampMixin):
    __tablename__ = "publications"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # stable ID or DOI hash
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Authors list stored as JSON: [{"name": "Ashish Vaswani", "researcher_id": "..."}, ...]
    authors: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    primary_institution_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    publication_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    venue: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    canonical_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Keywords / research topics
    keywords: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Provenance
    source_provider: Mapped[str] = mapped_column(
        String(100), default="synthetic", nullable=False, index=True
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    primary_institution: Mapped[Optional["Institution"]] = relationship(
        "Institution", back_populates="publications"
    )

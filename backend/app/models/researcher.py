"""Researcher database model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.institution import Institution


class Researcher(Base, TimestampMixin):
    __tablename__ = "researchers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # e.g., 'res_andrew_ng'
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    official_profile_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    institution_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Stored as JSON list of strings (e.g. ["Machine Learning", "Deep Learning", "Computer Vision"])
    research_interests: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    biography: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Verified public institutional contact only
    contact_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Provenance tracking
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    institution: Mapped["Institution"] = relationship("Institution", back_populates="researchers")

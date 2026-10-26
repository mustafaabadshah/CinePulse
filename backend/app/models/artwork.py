"""Media artwork metadata model for Tamasha catalog enrichment and review."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class MediaArtwork(Base, TimestampMixin):
    """Tracks verified and candidate artwork assets for programs, channels, and episodes."""
    __tablename__ = "media_artwork"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # 'program', 'episode', 'channel'
    artwork_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    artwork_source: Mapped[str] = mapped_column(String(64), default="child_episode", nullable=False)
    artwork_type: Mapped[str] = mapped_column(String(32), default="poster", nullable=False)  # 'poster', 'thumbnail', 'logo'
    verification_status: Mapped[str] = mapped_column(
        String(32), default="candidate", nullable=False, index=True
    )  # 'missing', 'candidate', 'verified', 'failed', 'manual_review_required'
    match_confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

"""Program and channel database model for media catalog enrichment."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.episode import Episode


class Program(Base, TimestampMixin):
    __tablename__ = "programs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # stable ID from prod_enrichment.csv
    type: Mapped[str] = mapped_column(String(32), default="program", nullable=False, index=True)  # 'program' | 'channel'
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    channel_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    info_language: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    info_genre: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    info_meta_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    info_content_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    info_staring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Provenance
    source_file: Mapped[str] = mapped_column(String(100), default="prod_enrichment.csv", nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    episodes: Mapped[List["Episode"]] = relationship(
        "Episode", back_populates="program", cascade="all, delete-orphan"
    )

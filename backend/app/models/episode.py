"""Episode database model for media catalog items."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.program import Program


class Episode(Base, TimestampMixin):
    __tablename__ = "episodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # stable ID from episodes_prod.csv
    program_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("programs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    raw_program_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    episode_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    views: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False, index=True)
    is_enable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Date fields
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    release_dt: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_dt: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Advertising & technical metadata
    ad_tag_url_android: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ad_tag_url_ios: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    channel_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    channel_status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    content_rating: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    content_tier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    hashtags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    insert_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_corrupt: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_latest: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_migrate: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_transcoded: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_vertical: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    is_zong_migrated: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manual_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    popularity_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sourcerecord: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    video_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Provenance
    source_file: Mapped[str] = mapped_column(String(100), default="episodes_prod.csv", nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    program: Mapped[Optional["Program"]] = relationship("Program", back_populates="episodes")

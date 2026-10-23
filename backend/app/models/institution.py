"""Institution database model."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.publication import Publication
    from app.models.researcher import Researcher


class Institution(Base, TimestampMixin):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )  # e.g., 'inst_mit', 'inst_stanford'
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ror_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)

    # Relationships
    researchers: Mapped[List["Researcher"]] = relationship(
        "Researcher", back_populates="institution", cascade="all, delete-orphan"
    )
    publications: Mapped[List["Publication"]] = relationship(
        "Publication", back_populates="primary_institution"
    )

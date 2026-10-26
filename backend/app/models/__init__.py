"""Export all SQLAlchemy models for easy import and Alembic metadata detection."""

from app.core.database import Base
from app.models.analytics import SearchAnalyticsEvent
from app.models.base import TimestampMixin
from app.models.episode import Episode
from app.models.import_job import ImportJob
from app.models.institution import Institution
from app.models.program import Program
from app.models.provenance import SourceRecord
from app.models.publication import Publication
from app.models.researcher import Researcher

__all__ = [
    "Base",
    "TimestampMixin",
    "Institution",
    "Researcher",
    "Publication",
    "Program",
    "Episode",
    "SourceRecord",
    "ImportJob",
    "SearchAnalyticsEvent",
]


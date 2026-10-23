"""Privacy-conscious search analytics database model."""

from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SearchAnalyticsEvent(Base):
    __tablename__ = "search_analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    query_text: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    index_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    filters_applied: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    zero_result: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

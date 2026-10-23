"""Pydantic schemas for Search Analytics."""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict


class SearchAnalyticsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query_text: str
    index_name: str
    filters_applied: Dict[str, Any]
    results_count: int
    latency_ms: float
    zero_result: bool
    timestamp: datetime


class SearchAnalyticsSummary(BaseModel):
    total_searches: int
    zero_result_searches: int
    zero_result_rate: float
    average_latency_ms: float
    p95_latency_ms: float
    top_queries: List[Dict[str, Any]]
    recent_searches: List[SearchAnalyticsRead]

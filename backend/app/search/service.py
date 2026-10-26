"""Search service executing media catalog queries against Meilisearch with safe allowlisted filters."""

import time
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.logging import logger
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.search.client import get_meili_client
from app.search.indexes import (
    INDEX_EPISODES,
    INDEX_PROGRAMS,
)
from meilisearch.client import Client
from sqlalchemy.orm import Session


class SearchService:
    def __init__(self, db: Session, client: Optional[Client] = None):
        self.db = db
        self.client = client or get_meili_client()

    def build_safe_filter_expression(
        self, filters: Dict[str, Any], allowed_fields: set
    ) -> Optional[str]:
        """Validates filter keys against an allowlist and builds a safe Meilisearch filter string."""
        if not filters:
            return None

        expressions = []
        for key, value in filters.items():
            if key not in allowed_fields:
                logger.warning(f"Rejected unallowed filter key: {key}")
                continue

            if value is None:
                continue

            # Handle boolean
            if isinstance(value, bool):
                expressions.append(f"{key} = {str(value).lower()}")
            # Handle integer/float
            elif isinstance(value, (int, float)):
                expressions.append(f"{key} = {value}")
            # Handle list/array (OR matching)
            elif isinstance(value, list) and value:
                sub_exprs = []
                for v in value:
                    escaped_v = str(v).replace('"', '\\"')
                    sub_exprs.append(f'{key} = "{escaped_v}"')
                expressions.append(f"({' OR '.join(sub_exprs)})")
            # Handle string
            elif isinstance(value, str) and value.strip():
                escaped_val = value.strip().replace('"', '\\"')
                expressions.append(f'{key} = "{escaped_val}"')

        return " AND ".join(expressions) if expressions else None

    def search(self, req: SearchRequest) -> SearchResponse:
        """Executes full-text search against the media catalog with allowlisted filters and facets."""
        start_time = time.perf_counter()
        target_type = req.type.lower()
        limit = min(req.limit, settings.max_search_limit)
        offset = max(0, req.offset)
        query = req.q.strip()

        hits: List[SearchResultItem] = []
        total_hits = 0
        facet_distribution: Dict[str, Dict[str, int]] = {}

        # -----------------------------------------------------------------
        # 1. Programs & Channels index query
        # -----------------------------------------------------------------
        if target_type in ("all", "programs", "channels"):
            filters_dict = dict(req.filters or {})
            if target_type == "channels":
                filters_dict["type"] = "channel"

            filter_str = self.build_safe_filter_expression(
                filters_dict, settings.allowed_program_filters
            )
            prog_limit = limit if target_type in ("programs", "channels") else min(limit, 6)
            prog_offset = offset if target_type in ("programs", "channels") else 0

            search_params: Dict[str, Any] = {
                "limit": prog_limit,
                "offset": prog_offset,
                "attributesToHighlight": [
                    "name",
                    "info_staring",
                    "info_genre",
                    "channel_name",
                    "info_meta_keywords",
                ],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
                "facets": ["type", "info_language", "channel_name", "info_content_type", "info_genre"],
            }
            if filter_str:
                search_params["filter"] = filter_str
            if req.sort and target_type in ("programs", "channels"):
                search_params["sort"] = [req.sort]

            try:
                res = self.client.index(INDEX_PROGRAMS).search(query, search_params)
                prog_total = res.get("estimatedTotalHits", len(res.get("hits", [])))
                total_hits += prog_total

                if "facetDistribution" in res:
                    for facet_k, facet_v in res["facetDistribution"].items():
                        facet_distribution.setdefault(facet_k, {}).update(facet_v)

                for item in res.get("hits", []):
                    formatted = item.get("_formatted", {})
                    chan_str = item.get("channel_name") or ""
                    lang_str = item.get("info_language") or ""
                    ctype_str = item.get("info_content_type") or ""
                    sub_parts = [p for p in [chan_str, lang_str, ctype_str] if p]
                    subtitle = " • ".join(sub_parts) if sub_parts else item.get("type", "program").title()

                    cast_str = item.get("info_staring")
                    snippet = f"Starring: {cast_str}" if cast_str else (item.get("info_meta_keywords") or "")
                    tags = item.get("genre_list") or ([item.get("info_genre")] if item.get("info_genre") else [])

                    hits.append(
                        SearchResultItem(
                            id=item["id"],
                            type="program",
                            title=item["name"],
                            subtitle=subtitle,
                            snippet=snippet,
                            tags=tags,
                            source_url=item.get("thumbnail"),
                            thumbnail=item.get("thumbnail"),
                            channel_name=item.get("channel_name"),
                            program_name=item.get("name"),
                            raw=item,
                            formatted=formatted,
                        )
                    )
            except Exception as e:
                logger.error(f"Error querying program index: {e}")

        # -----------------------------------------------------------------
        # 2. Episodes index query
        # -----------------------------------------------------------------
        if target_type in ("all", "episodes"):
            filter_str = self.build_safe_filter_expression(
                req.filters or {}, settings.allowed_episode_filters
            )
            ep_limit = limit if target_type == "episodes" else limit
            ep_offset = offset if target_type == "episodes" else 0

            search_params = {
                "limit": ep_limit,
                "offset": ep_offset,
                "attributesToHighlight": [
                    "title",
                    "program_name",
                    "stars",
                    "genre",
                    "description",
                    "channel_name",
                ],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
                "facets": [
                    "is_free",
                    "content_tier",
                    "genre",
                    "language",
                    "channel_name",
                    "region",
                    "is_vertical",
                ],
            }
            if filter_str:
                search_params["filter"] = filter_str
            if req.sort and target_type == "episodes":
                search_params["sort"] = [req.sort]

            try:
                res = self.client.index(INDEX_EPISODES).search(query, search_params)
                ep_total = res.get("estimatedTotalHits", len(res.get("hits", [])))
                total_hits += ep_total

                if "facetDistribution" in res:
                    for facet_k, facet_v in res["facetDistribution"].items():
                        facet_distribution.setdefault(facet_k, {}).update(facet_v)

                for item in res.get("hits", []):
                    formatted = item.get("_formatted", {})
                    prog_str = item.get("program_name") or ""
                    chan_str = item.get("channel_name") or ""
                    dur_str = item.get("duration") or ""
                    subtitle_parts = [p for p in [prog_str, chan_str, dur_str] if p]
                    subtitle = " • ".join(subtitle_parts) if subtitle_parts else "Episode"
                    tags = item.get("genre_list") or ([item.get("genre")] if item.get("genre") else [])

                    hits.append(
                        SearchResultItem(
                            id=item["id"],
                            type="episode",
                            title=item["title"],
                            subtitle=subtitle,
                            snippet=item.get("description", ""),
                            tags=tags,
                            source_url=item.get("thumbnail"),
                            thumbnail=item.get("thumbnail"),
                            views=item.get("views"),
                            duration=item.get("duration"),
                            duration_seconds=item.get("duration_seconds"),
                            is_free=item.get("is_free"),
                            content_tier=item.get("content_tier"),
                            channel_name=item.get("channel_name"),
                            program_name=item.get("program_name"),
                            raw=item,
                            formatted=formatted,
                        )
                    )
            except Exception as e:
                logger.error(f"Error querying episode index: {e}")

        # Compute elapsed time
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Slice unified results if "all"
        if target_type == "all":
            final_hits = hits[offset : offset + limit]
        else:
            final_hits = hits

        page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_hits + limit - 1) // limit if limit > 0 else 1

        return SearchResponse(
            query=query,
            type=target_type,
            total_hits=total_hits,
            offset=offset,
            limit=limit,
            page=page,
            total_pages=total_pages,
            processing_time_ms=duration_ms,
            hits=final_hits,
            facet_distribution=facet_distribution,
        )

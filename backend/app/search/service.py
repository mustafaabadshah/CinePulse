"""Search service executing queries against Meilisearch with allowlisted filters and analytics recording."""

import time
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.logging import logger
from app.models.analytics import SearchAnalyticsEvent
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.search.client import get_meili_client
from app.search.indexes import (
    INDEX_EPISODES,
    INDEX_INSTITUTIONS,
    INDEX_PROGRAMS,
    INDEX_PUBLICATIONS,
    INDEX_RESEARCHERS,
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
        """Executes search with allowlisted filtering, sorting, pagination, and analytics tracking."""
        start_time = time.perf_counter()
        target_type = req.type.lower()
        limit = min(req.limit, settings.max_search_limit)
        offset = max(0, req.offset)
        query = req.q.strip()

        hits: List[SearchResultItem] = []
        total_hits = 0
        facet_distribution: Dict[str, Dict[str, int]] = {}

        # 1. Researcher index query
        if target_type in ("all", "researchers"):
            filter_str = self.build_safe_filter_expression(
                req.filters or {}, settings.allowed_researcher_filters
            )
            search_params: Dict[str, Any] = {
                "limit": limit if target_type == "researchers" else min(limit, 10),
                "offset": offset if target_type == "researchers" else 0,
                "attributesToHighlight": [
                    "full_name",
                    "research_interests",
                    "biography",
                    "institution_name",
                ],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
                "facets": ["country", "institution_name", "research_interests", "is_synthetic"],
            }
            if filter_str:
                search_params["filter"] = filter_str
            if req.sort and target_type == "researchers":
                search_params["sort"] = [req.sort]

            try:
                res = self.client.index(INDEX_RESEARCHERS).search(query, search_params)
                total_hits += res.get("estimatedTotalHits", len(res.get("hits", [])))
                if "facetDistribution" in res:
                    for facet_k, facet_v in res["facetDistribution"].items():
                        facet_distribution.setdefault(facet_k, {}).update(facet_v)

                for item in res.get("hits", []):
                    formatted = item.get("_formatted", {})
                    hits.append(
                        SearchResultItem(
                            id=item["id"],
                            type="researcher",
                            title=item["full_name"],
                            subtitle=f"{item.get('institution_name', '')} • {item.get('country', '')}",
                            snippet=item.get("biography", ""),
                            tags=item.get("research_interests", []),
                            source_url=item.get("official_profile_url")
                            or item.get("contact_source_url"),
                            is_synthetic=item.get("is_synthetic", False),
                            raw=item,
                            formatted=formatted,
                        )
                    )
            except Exception as e:
                logger.error(f"Error querying researcher index: {e}")

        # 2. Publication index query
        if target_type in ("all", "publications"):
            filter_str = self.build_safe_filter_expression(
                req.filters or {}, settings.allowed_publication_filters
            )
            search_params = {
                "limit": limit if target_type == "publications" else min(limit, 10),
                "offset": offset if target_type == "publications" else 0,
                "attributesToHighlight": ["title", "abstract", "keywords", "authors", "venue"],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
                "facets": [
                    "publication_year",
                    "venue",
                    "keywords",
                    "source_provider",
                    "is_synthetic",
                ],
            }
            if filter_str:
                search_params["filter"] = filter_str
            if req.sort and target_type == "publications":
                search_params["sort"] = [req.sort]

            try:
                res = self.client.index(INDEX_PUBLICATIONS).search(query, search_params)
                total_hits += res.get("estimatedTotalHits", len(res.get("hits", [])))
                if "facetDistribution" in res:
                    for facet_k, facet_v in res["facetDistribution"].items():
                        facet_distribution.setdefault(facet_k, {}).update(facet_v)

                for item in res.get("hits", []):
                    formatted = item.get("_formatted", {})
                    authors_str = ", ".join(item.get("authors", []))
                    venue_str = item.get("venue") or ""
                    year_str = str(item.get("publication_year", ""))
                    subtitle = (
                        f"{authors_str} • {venue_str} ({year_str})" if venue_str else authors_str
                    )
                    hits.append(
                        SearchResultItem(
                            id=item["id"],
                            type="publication",
                            title=item["title"],
                            subtitle=subtitle,
                            snippet=item.get("abstract", ""),
                            tags=item.get("keywords", []),
                            source_url=item.get("canonical_url")
                            or (f"https://doi.org/{item['doi']}" if item.get("doi") else None),
                            is_synthetic=item.get("is_synthetic", False),
                            raw=item,
                            formatted=formatted,
                        )
                    )
            except Exception as e:
                logger.error(f"Error querying publication index: {e}")

        # 3. Institution index query
        if target_type in ("all", "institutions"):
            filter_str = self.build_safe_filter_expression(
                req.filters or {}, settings.allowed_institution_filters
            )
            search_params = {
                "limit": limit if target_type == "institutions" else min(limit, 5),
                "offset": offset if target_type == "institutions" else 0,
                "attributesToHighlight": ["name", "city", "country"],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
                "facets": ["country", "city"],
            }
            if filter_str:
                search_params["filter"] = filter_str
            if req.sort and target_type == "institutions":
                search_params["sort"] = [req.sort]

            try:
                res = self.client.index(INDEX_INSTITUTIONS).search(query, search_params)
                total_hits += res.get("estimatedTotalHits", len(res.get("hits", [])))
                if "facetDistribution" in res:
                    for facet_k, facet_v in res["facetDistribution"].items():
                        facet_distribution.setdefault(facet_k, {}).update(facet_v)

                for item in res.get("hits", []):
                    formatted = item.get("_formatted", {})
                    hits.append(
                        SearchResultItem(
                            id=item["id"],
                            type="institution",
                            title=item["name"],
                            subtitle=f"{item.get('city', '')}, {item.get('country', '')}",
                            snippet=f"Research institution located in {item.get('city')}, {item.get('country')}.",
                            tags=[item.get("country", "")],
                            source_url=item.get("website_url"),
                            is_synthetic=False,
                            raw=item,
                            formatted=formatted,
                        )
                    )
            except Exception as e:
                logger.error(f"Error querying institution index: {e}")

        # 4. Episode index query
        if target_type in ("all", "episodes"):
            filter_str = self.build_safe_filter_expression(
                req.filters or {}, settings.allowed_episode_filters
            )
            search_params = {
                "limit": limit if target_type == "episodes" else min(limit, 10),
                "offset": offset if target_type == "episodes" else 0,
                "attributesToHighlight": ["title", "program_name", "stars", "genre", "description", "channel_name"],
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
                total_hits += res.get("estimatedTotalHits", len(res.get("hits", [])))
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
                            is_synthetic=False,
                            raw=item,
                            formatted=formatted,
                        )
                    )
            except Exception as e:
                logger.error(f"Error querying episode index: {e}")

        # 5. Program index query
        if target_type in ("all", "programs"):
            filter_str = self.build_safe_filter_expression(
                req.filters or {}, settings.allowed_program_filters
            )
            search_params = {
                "limit": limit if target_type == "programs" else min(limit, 10),
                "offset": offset if target_type == "programs" else 0,
                "attributesToHighlight": ["name", "info_staring", "info_genre", "channel_name"],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
                "facets": ["type", "info_language", "channel_name", "info_content_type"],
            }
            if filter_str:
                search_params["filter"] = filter_str
            if req.sort and target_type == "programs":
                search_params["sort"] = [req.sort]

            try:
                res = self.client.index(INDEX_PROGRAMS).search(query, search_params)
                total_hits += res.get("estimatedTotalHits", len(res.get("hits", [])))
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
                            source_url=None,
                            is_synthetic=False,
                            raw=item,
                            formatted=formatted,
                        )
                    )
            except Exception as e:
                logger.error(f"Error querying program index: {e}")


        # Compute elapsed time
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Slice unified results if "all"
        if target_type == "all":
            final_hits = hits[offset : offset + limit]
        else:
            final_hits = hits

        page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_hits + limit - 1) // limit if limit > 0 else 1

        # Record privacy-conscious analytics event
        try:
            event = SearchAnalyticsEvent(
                query_text=query or "*",
                index_name=target_type,
                filters_applied=req.filters or {},
                results_count=total_hits,
                latency_ms=duration_ms,
                zero_result=(total_hits == 0),
            )
            self.db.add(event)
            self.db.commit()
        except Exception as err:
            logger.warning(f"Failed to record search analytics: {err}")

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

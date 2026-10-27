"""Search service executing media catalog queries against Meilisearch with safe allowlisted filters and spaCy NLP grounding."""

from __future__ import annotations

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
from app.services.nlp.schemas import QueryInterpretation
from app.services.nlp.service import NLPService, nlp_service as default_nlp_service
from meilisearch.client import Client
from sqlalchemy.orm import Session


class SearchService:
    def __init__(
        self,
        db: Session,
        client: Optional[Client] = None,
        nlp_service: Optional[NLPService] = None,
    ):
        self.db = db
        self.client = client or get_meili_client()
        self.nlp = nlp_service or default_nlp_service

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
        """Executes search against the media catalog with spaCy NLP query understanding and allowlisted filters."""
        start_time = time.perf_counter()
        target_type = req.type.lower()
        limit = min(req.limit, settings.max_search_limit)
        offset = max(0, req.offset)
        raw_query = req.q.strip()

        # -----------------------------------------------------------------
        # 1. NLP Query Interpretation & Entity Grounding
        # -----------------------------------------------------------------
        interpretation: Optional[QueryInterpretation] = None
        if raw_query and not req.disable_nlp and self.nlp:
            try:
                interpretation = self.nlp.parse_query(raw_query)
            except Exception as nlp_exc:
                logger.warning(f"Error during NLP query interpretation for '{raw_query}': {nlp_exc}")

        # Determine queries and inferred filters
        is_assisted = bool(interpretation and interpretation.is_nlp_assisted)
        prog_query = raw_query
        ep_query = raw_query

        prog_inferred_filters: Dict[str, Any] = {}
        ep_inferred_filters: Dict[str, Any] = {}

        if is_assisted and interpretation:
            # 1. Programs index filtering
            if interpretation.matched_channel:
                prog_inferred_filters["channel_name"] = interpretation.matched_channel
            if interpretation.matched_genres:
                prog_inferred_filters["genre_list"] = (
                    [g.lower() for g in interpretation.matched_genres]
                    if len(interpretation.matched_genres) > 1
                    else interpretation.matched_genres[0].lower()
                )
            elif interpretation.matched_genre:
                prog_inferred_filters["genre_list"] = interpretation.matched_genre.lower()
            if interpretation.matched_content_type:
                prog_inferred_filters["content_type_list"] = interpretation.matched_content_type.lower()
            if interpretation.matched_language:
                prog_inferred_filters["info_language"] = interpretation.matched_language.lower()
            if interpretation.matched_person:
                prog_inferred_filters["starring_list"] = interpretation.matched_person

            # 2. Episodes index filtering
            if interpretation.matched_program_id:
                ep_inferred_filters["program_id"] = interpretation.matched_program_id
            if interpretation.matched_channel:
                ep_inferred_filters["channel_name"] = interpretation.matched_channel
            if interpretation.matched_genres:
                ep_inferred_filters["genre_list"] = (
                    [g.lower() for g in interpretation.matched_genres]
                    if len(interpretation.matched_genres) > 1
                    else interpretation.matched_genres[0].lower()
                )
            elif interpretation.matched_genre:
                ep_inferred_filters["genre_list"] = interpretation.matched_genre.lower()
            if interpretation.matched_content_type:
                ep_inferred_filters["content_type_list"] = interpretation.matched_content_type.lower()
            if interpretation.matched_language:
                ep_inferred_filters["language"] = interpretation.matched_language.lower()
            if interpretation.episode_number is not None:
                ep_inferred_filters["episode_number"] = interpretation.episode_number
            if interpretation.matched_person:
                ep_inferred_filters["stars_list"] = interpretation.matched_person

            # 3. Combined query routing between semantic filters and text search
            if interpretation.matched_program_name and not interpretation.remaining_query:
                # Fully identified show title (e.g., "Ehd E Wafa" or "Parizaad")
                prog_query = interpretation.matched_program_name
                # If episode program_id filter is applied, query "" retrieves episodes ordered by sequence
                ep_query = "" if interpretation.matched_program_id else interpretation.matched_program_name
            elif interpretation.remaining_query:
                # Specific keywords alongside filters (e.g. "funny pakistani movie", "live stream", "car review")
                prog_query = interpretation.remaining_query
                ep_query = interpretation.remaining_query
            elif interpretation.matched_program_id or interpretation.episode_number is not None:
                prog_query = interpretation.matched_program_name or ""
                ep_query = ""
            elif prog_inferred_filters or ep_inferred_filters:
                # Pure semantic intent (e.g. "funny movie" -> genre=comedy, content_type=movie)
                prog_query = ""
                ep_query = ""
            else:
                prog_query = interpretation.normalized_query
                ep_query = interpretation.normalized_query

        # -----------------------------------------------------------------
        # 2. Execute Primary Search
        # -----------------------------------------------------------------
        hits, total_hits, facet_dist = self._execute_search_passes(
            target_type=target_type,
            limit=limit,
            offset=offset,
            raw_filters=req.filters or {},
            sort=req.sort,
            prog_query=prog_query,
            ep_query=ep_query,
            prog_inferred_filters=prog_inferred_filters,
            ep_inferred_filters=ep_inferred_filters,
        )

        # -----------------------------------------------------------------
        # 3. Safe Fallback to Plain Text if Assisted Search Produced Zero Hits
        # -----------------------------------------------------------------
        used_fallback = False
        if is_assisted and total_hits == 0 and raw_query:
            logger.info(f"Assisted search produced 0 hits for '{raw_query}'. Falling back to baseline search.")
            hits, total_hits, facet_dist = self._execute_search_passes(
                target_type=target_type,
                limit=limit,
                offset=offset,
                raw_filters=req.filters or {},
                sort=req.sort,
                prog_query=raw_query,
                ep_query=raw_query,
                prog_inferred_filters={},
                ep_inferred_filters={},
            )
            used_fallback = True

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Slice unified results if "all"
        final_hits = hits[offset : offset + limit] if target_type == "all" else hits
        page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_hits + limit - 1) // limit if limit > 0 else 1

        nlp_payload = None
        if interpretation:
            nlp_payload = interpretation.model_dump()
            if used_fallback:
                nlp_payload["fallback_applied"] = True

        return SearchResponse(
            query=raw_query,
            type=target_type,
            total_hits=total_hits,
            offset=offset,
            limit=limit,
            page=page,
            total_pages=total_pages,
            processing_time_ms=duration_ms,
            hits=final_hits,
            facet_distribution=facet_dist,
            nlp=nlp_payload,
        )

    def _execute_search_passes(
        self,
        target_type: str,
        limit: int,
        offset: int,
        raw_filters: Dict[str, Any],
        sort: Optional[str],
        prog_query: str,
        ep_query: str,
        prog_inferred_filters: Dict[str, Any],
        ep_inferred_filters: Dict[str, Any],
    ) -> tuple[List[SearchResultItem], int, Dict[str, Dict[str, int]]]:
        """Executes index queries against programs and episodes with specific filters."""
        hits: List[SearchResultItem] = []
        total_hits = 0
        facet_distribution: Dict[str, Dict[str, int]] = {}

        # -----------------------------------------------------------------
        # Programs & Channels pass
        # -----------------------------------------------------------------
        if target_type in ("all", "programs", "channels"):
            combined_filters = {**prog_inferred_filters, **raw_filters}
            if target_type == "channels":
                combined_filters["type"] = "channel"

            filter_str = self.build_safe_filter_expression(
                combined_filters, settings.allowed_program_filters
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
            if sort and target_type in ("programs", "channels"):
                search_params["sort"] = [sort]

            try:
                res = self.client.index(INDEX_PROGRAMS).search(prog_query, search_params)
                prog_total = res.get("estimatedTotalHits", len(res.get("hits", [])))
                total_hits += prog_total

                if "facetDistribution" in res:
                    for facet_k, facet_v in res["facetDistribution"].items():
                        norm_k = "language" if facet_k == "info_language" else ("genre" if facet_k == "info_genre" else facet_k)
                        if norm_k not in facet_distribution:
                            facet_distribution[norm_k] = {}
                        for val_k, val_cnt in facet_v.items():
                            facet_distribution[norm_k][val_k] = facet_distribution[norm_k].get(val_k, 0) + val_cnt

                for item in res.get("hits", []):
                    formatted = item.get("_formatted", {})
                    chan_str = item.get("channel_name") or ""
                    lang_str = item.get("info_language") or ""
                    ctype_str = item.get("info_content_type") or ""
                    sub_parts = [p for p in [chan_str, lang_str, ctype_str] if p]
                    subtitle = " • ".join(sub_parts) if sub_parts else item.get("type", "program").title()

                    cast_str = item.get("info_staring")
                    snippet = item.get("info_meta_keywords") or ""
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
                            program_name=None,
                            raw=item,
                            formatted=formatted,
                        )
                    )
            except Exception as e:
                logger.error(f"Error querying program index: {e}")

        # -----------------------------------------------------------------
        # Episodes pass
        # -----------------------------------------------------------------
        if target_type in ("all", "episodes"):
            combined_filters = {**ep_inferred_filters, **raw_filters}
            filter_str = self.build_safe_filter_expression(
                combined_filters, settings.allowed_episode_filters
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
            if sort and target_type == "episodes":
                search_params["sort"] = [sort]

            try:
                res = self.client.index(INDEX_EPISODES).search(ep_query, search_params)
                ep_total = res.get("estimatedTotalHits", len(res.get("hits", [])))
                total_hits += ep_total

                if "facetDistribution" in res:
                    for facet_k, facet_v in res["facetDistribution"].items():
                        if facet_k not in facet_distribution:
                            facet_distribution[facet_k] = {}
                        for val_k, val_cnt in facet_v.items():
                            facet_distribution[facet_k][val_k] = facet_distribution[facet_k].get(val_k, 0) + val_cnt

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

        return hits, total_hits, facet_distribution

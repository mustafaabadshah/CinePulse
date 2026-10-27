"""Query interpretation and entity parsing logic combining spaCy and catalog grounding."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import spacy
from spacy.tokens import Doc

from app.core.logging import logger
from app.services.nlp.catalog_entities import CatalogKnowledgeBase
from app.services.nlp.normalization import canonical_key, normalize_query_text
from app.services.nlp.schemas import EntityType, ExtractedEntity, QueryInterpretation


# Regexes for episode sequence extraction
# Matches: "Episode 3", "Ep 03", "EP 2", "eps 14", "Part 2", "S01E04", "Season 1 Episode 4"
_EPISODE_PATTERNS = [
    re.compile(r"\b(?:season\s*\d+\s+)?(?:episode|episodes|ep|eps|part)\s*[:#.\-]?\s*(\d+)\b", re.IGNORECASE),
    re.compile(r"\bs\d+e(\d+)\b", re.IGNORECASE),
    re.compile(r"\bep\.?\s*(\d+)\b", re.IGNORECASE),
]

# Patterns for conversational intent, stop-words, and OTT discovery fillers
_CONVERSATIONAL_INTENT_PATTERNS = [
    re.compile(
        r"\b(?:i\s+(?:want|would\s+like|need)\s+to\s+(?:watch|see|stream|find|play|get)|can\s+(?:i|you)\s+(?:show|watch|find|play|stream)|please\s+(?:show|play|find|stream)|show\s+me|find\s+me|search\s+for|looking\s+for|give\s+me|stream|watch|play|something)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:online|stream|hd|watch|free)\b", re.IGNORECASE),
]

_DANGLING_PUNCT_RE = re.compile(r"^[^\w\s]+|[^\w\s]+$")
_DANGLING_PREPOSITIONS_RE = re.compile(
    r"^(?:with|starring|featuring|in|of|by|about|and|or|for)\s+|\s+(?:with|starring|featuring|in|of|by|about|and|or|for)$",
    re.IGNORECASE,
)
_WHITESPACE_RE = re.compile(r"\s+")


class QueryParser:
    """Parses raw user queries into grounded, structured QueryInterpretation objects."""

    def __init__(
        self,
        nlp: Optional[spacy.language.Language],
        kb: CatalogKnowledgeBase,
        confidence_threshold: float = 0.6,
        max_query_length: int = 200,
    ):
        self.nlp = nlp
        self.kb = kb
        self.confidence_threshold = confidence_threshold
        self.max_query_length = max_query_length

    def parse(self, query: str) -> QueryInterpretation:
        """Parses a search query into structured entities and filters.
        
        Guaranteed to never raise an unhandled exception: falls back safely to
        a clean plain-text interpretation if any step encounters unexpected data.
        """
        start_time = time.perf_counter()
        raw_query = query or ""
        
        # 1. Truncate query length for safety
        bounded_query = raw_query[:self.max_query_length]
        norm_query = normalize_query_text(bounded_query)

        if not norm_query:
            return QueryInterpretation(
                original_query=raw_query,
                normalized_query="",
                remaining_query="",
                is_nlp_assisted=False,
                diagnostics={"latency_ms": 0.0, "reason": "empty_query"},
            )

        extracted_entities: List[ExtractedEntity] = []
        consumed_char_spans: List[Tuple[int, int]] = []
        episode_number: Optional[int] = None

        # 2. Extract Episode Number via regex
        for pattern in _EPISODE_PATTERNS:
            match = pattern.search(norm_query)
            if match:
                try:
                    num_val = int(match.group(1))
                    if 0 < num_val <= 9999:  # realistic catalog episode bounds
                        episode_number = num_val
                        span_start, span_end = match.span()
                        consumed_char_spans.append((span_start, span_end))
                        extracted_entities.append(
                            ExtractedEntity(
                                text=match.group(0),
                                label=EntityType.EPISODE_NUMBER.value,
                                start_char=span_start,
                                end_char=span_end,
                                confidence=1.0,
                                source="rule_regex",
                                canonical_name=f"Episode {num_val}",
                                metadata={"number": num_val},
                            )
                        )
                        break
                except (ValueError, IndexError):
                    pass

        # 2b. Consume conversational intent and OTT stop-words so they don't leak into remaining_query
        for intent_pat in _CONVERSATIONAL_INTENT_PATTERNS:
            for match in intent_pat.finditer(norm_query):
                consumed_char_spans.append(match.span())

        # 3. Extract Named Entities via spaCy (if model is available)
        matched_program_id: Optional[str] = None
        matched_program_name: Optional[str] = None
        matched_channel: Optional[str] = None
        matched_genre: Optional[str] = None
        matched_genres: List[str] = []
        matched_content_type: Optional[str] = None
        matched_person: Optional[str] = None
        matched_language: Optional[str] = None

        if self.nlp is not None:
            try:
                doc: Doc = self.nlp(norm_query)
                for ent in doc.ents:
                    ent_text = ent.text.strip()
                    ent_key = canonical_key(ent_text)
                    if not ent_key:
                        continue

                    # Check overlap with already consumed spans (e.g. episode sequence)
                    if any(
                        (ent.start_char < c_end and ent.end_char > c_start)
                        for c_start, c_end in consumed_char_spans
                    ):
                        continue

                    label = ent.label_
                    resolved_id = None
                    canonical_name = None
                    confidence = 1.0

                    if label == EntityType.PROGRAM_TITLE.value:
                        prog_info = self.kb.programs_by_key.get(ent_key)
                        if prog_info:
                            resolved_id = prog_info["id"]
                            canonical_name = prog_info["name"]
                            matched_program_id = resolved_id
                            matched_program_name = canonical_name
                        else:
                            # Fuzzy/statistical fallback
                            confidence = 0.75
                            canonical_name = ent_text

                    elif label == EntityType.CHANNEL.value:
                        chan_name = self.kb.channels_by_key.get(ent_key)
                        if chan_name:
                            canonical_name = chan_name
                            resolved_id = chan_name
                            matched_channel = chan_name
                        else:
                            confidence = 0.75

                    elif label == EntityType.GENRE.value:
                        genre_name = self.kb.genres_by_key.get(ent_key)
                        if genre_name:
                            canonical_name = genre_name
                            resolved_id = genre_name
                            matched_genre = genre_name
                            if genre_name not in matched_genres:
                                matched_genres.append(genre_name)
                        else:
                            confidence = 0.75

                    elif label == EntityType.CONTENT_TYPE.value:
                        ct_name = self.kb.content_types_by_key.get(ent_key)
                        if ct_name:
                            canonical_name = ct_name
                            resolved_id = ct_name
                            matched_content_type = ct_name

                    elif label == EntityType.LANGUAGE.value:
                        lang_name = self.kb.languages_by_key.get(ent_key)
                        if lang_name:
                            canonical_name = lang_name
                            resolved_id = lang_name
                            matched_language = lang_name

                    elif label == EntityType.PERSON.value:
                        actor_name = self.kb.actors_by_key.get(ent_key)
                        if actor_name:
                            canonical_name = actor_name
                            resolved_id = actor_name
                            matched_person = actor_name

                    if confidence >= self.confidence_threshold:
                        consumed_char_spans.append((ent.start_char, ent.end_char))
                        extracted_entities.append(
                            ExtractedEntity(
                                text=ent_text,
                                label=label,
                                start_char=ent.start_char,
                                end_char=ent.end_char,
                                confidence=confidence,
                                source="spacy_catalog",
                                resolved_id=resolved_id,
                                canonical_name=canonical_name or ent_text,
                            )
                        )

            except Exception as exc:
                logger.warning(f"Error during spaCy NER processing for query '{norm_query}': {exc}")

        # 4. Fallback direct catalog dictionary scan if no program entity was recognized
        if not matched_program_id:
            # Check full normalized query or subphrases
            query_key = canonical_key(norm_query)
            if query_key in self.kb.programs_by_key:
                prog_info = self.kb.programs_by_key[query_key]
                matched_program_id = prog_info["id"]
                matched_program_name = prog_info["name"]
                extracted_entities.append(
                    ExtractedEntity(
                        text=norm_query,
                        label=EntityType.PROGRAM_TITLE.value,
                        start_char=0,
                        end_char=len(norm_query),
                        confidence=1.0,
                        source="catalog_exact",
                        resolved_id=matched_program_id,
                        canonical_name=matched_program_name,
                    )
                )
                consumed_char_spans.append((0, len(norm_query)))

        # 5. Compute Remaining Query text
        remaining_query = self._compute_remaining_query(norm_query, consumed_char_spans)

        # 6. Build Safe Inferred Filters
        inferred_filters: Dict[str, Any] = {}
        if matched_program_id:
            inferred_filters["program_id"] = matched_program_id
        if matched_channel:
            inferred_filters["channel_name"] = matched_channel
        if matched_genres:
            inferred_filters["genre_list"] = (
                [g.lower() for g in matched_genres] if len(matched_genres) > 1 else matched_genres[0].lower()
            )
        elif matched_genre:
            inferred_filters["genre_list"] = matched_genre.lower()
        if matched_content_type:
            inferred_filters["content_type_list"] = matched_content_type.lower()
        if matched_language:
            inferred_filters["info_language"] = matched_language.lower()
        if episode_number is not None:
            inferred_filters["episode_number"] = episode_number
        if matched_person:
            inferred_filters["starring_list"] = matched_person

        is_nlp_assisted = bool(extracted_entities or episode_number is not None)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        return QueryInterpretation(
            original_query=raw_query,
            normalized_query=norm_query,
            recognized_entities=extracted_entities,
            episode_number=episode_number,
            matched_program_id=matched_program_id,
            matched_program_name=matched_program_name,
            matched_genre=matched_genre,
            matched_genres=matched_genres,
            matched_channel=matched_channel,
            matched_content_type=matched_content_type,
            matched_person=matched_person,
            matched_language=matched_language,
            remaining_query=remaining_query,
            inferred_filters=inferred_filters,
            is_nlp_assisted=is_nlp_assisted,
            model_name=self.nlp.meta.get("name") if self.nlp else None,
            diagnostics={
                "latency_ms": elapsed_ms,
                "spans_consumed": len(consumed_char_spans),
                "entities_count": len(extracted_entities),
            },
        )

    def _compute_remaining_query(
        self, text: str, spans: List[Tuple[int, int]]
    ) -> str:
        """Removes consumed character spans from query text without leaving orphaned punctuation."""
        if not spans:
            return text

        # Sort spans by start offset
        sorted_spans = sorted(spans, key=lambda s: s[0])
        chunks = []
        last_idx = 0
        for start, end in sorted_spans:
            if start > last_idx:
                chunks.append(text[last_idx:start])
            last_idx = max(last_idx, end)
        if last_idx < len(text):
            chunks.append(text[last_idx:])

        remaining = " ".join(chunks)
        # Clean up stray punctuation and whitespace
        remaining = _WHITESPACE_RE.sub(" ", remaining).strip()
        remaining = _DANGLING_PUNCT_RE.sub("", remaining).strip()
        # Clean dangling prepositions like "with", "starring", "about"
        remaining = _DANGLING_PREPOSITIONS_RE.sub("", remaining).strip()
        remaining = _DANGLING_PUNCT_RE.sub("", remaining).strip()
        return remaining

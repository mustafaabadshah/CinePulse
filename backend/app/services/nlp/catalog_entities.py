"""Catalog-aware entity pattern builder for CinePulse spaCy EntityRuler."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.program import Program
from app.services.data_normalizer import clean_str, split_tags
from app.services.nlp.normalization import canonical_key, normalize_query_text
from app.services.nlp.schemas import EntityType


# Words too ambiguous or generic to treat as standalone program titles or entities
_EXCLUDED_SHORT_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of",
    "by", "with", "is", "it", "as", "tv", "hd", "live", "show", "shows",
    "all", "new", "top", "ep", "eps", "episode", "part", "season"
}

# Semantic OTT synonyms mapping common conversational phrases to catalog genres & content types
OTT_INTENT_SYNONYMS = [
    # Comedy
    (EntityType.GENRE, ["funny", "hilarious", "humor", "humorous", "comedy", "comedies", "jokes", "standup", "fun"], "Comedy"),
    # Horror
    (EntityType.GENRE, ["horror", "scary", "spooky", "creepy", "ghost", "haunted"], "Horror"),
    # Romance
    (EntityType.GENRE, ["romance", "romantic", "love story", "love stories", "ishq", "pyar"], "Romance"),
    # Action & Thriller
    (EntityType.GENRE, ["action", "thriller", "suspense", "mystery", "fight"], "Action"),
    # Crime
    (EntityType.GENRE, ["crime", "murder", "police", "investigation", "detective"], "Crime"),
    # Kids
    (EntityType.GENRE, ["kids", "children", "cartoon", "cartoons", "animated", "animation"], "Kids"),
    # News
    (EntityType.GENRE, ["news", "bulletin", "khabar", "khabrain", "current affairs"], "News"),
    # Sports
    (EntityType.GENRE, ["sports", "cricket", "match", "tournament", "championship", "psl", "world cup"], "Sports"),
    # Drama
    (EntityType.GENRE, ["drama", "dramas", "serial", "serials", "soap"], "Drama"),
    
    # Content Types / Formats
    (EntityType.CONTENT_TYPE, ["movie", "movies", "film", "films", "cinema", "feature film"], "movie"),
    (EntityType.CONTENT_TYPE, ["telefilm", "telefilms", "tv film"], "telefilm"),
    (EntityType.CONTENT_TYPE, ["short film", "short films", "shorts"], "short film"),
    (EntityType.CONTENT_TYPE, ["series", "tv series", "tv show", "web series"], "series"),
    (EntityType.CONTENT_TYPE, ["podcast", "podcasts"], "podcast"),
    (EntityType.CONTENT_TYPE, ["trailer", "trailers", "teaser", "teasers", "promo", "promos"], "teaser"),
    (EntityType.CONTENT_TYPE, ["song", "songs", "music", "ost", "music video"], "music"),
]


@dataclass
class CatalogKnowledgeBase:
    """In-memory grounded entity catalog for fast resolution and spaCy rule matching."""
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    programs_by_key: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    programs_by_id: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    channels_by_key: Dict[str, str] = field(default_factory=dict)
    genres_by_key: Dict[str, str] = field(default_factory=dict)
    content_types_by_key: Dict[str, str] = field(default_factory=dict)
    languages_by_key: Dict[str, str] = field(default_factory=dict)
    actors_by_key: Dict[str, str] = field(default_factory=dict)
    built_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_patterns(self) -> int:
        return len(self.patterns)


def build_catalog_knowledge_base(
    db: Session,
    max_patterns: int = 5000,
) -> CatalogKnowledgeBase:
    """Builds deduplicated, grounded entity recognition rules from SQLite catalog metadata.
    
    Extracts:
    - PROGRAM_TITLE: Canonical program names & slugs (e.g. Ehd E Wafa, Parizaad)
    - CHANNEL: Broadcast network names (e.g. Hum News, TV One, 24 News HD)
    - GENRE: Verified genres (e.g. Drama, News, Comedy, Crime, Sports)
    - CONTENT_TYPE: Verified content formats (e.g. series, talk show, telefilm)
    - LANGUAGE: Media languages (e.g. Urdu, English, Punjabi)
    - PERSON: Lead cast/starring names from info_staring
    """
    kb = CatalogKnowledgeBase()
    patterns: List[Dict[str, Any]] = []
    seen_pattern_keys: Set[str] = set()

    def add_pattern(text: str, label: EntityType, entity_id: str, canonical_name: str) -> None:
        norm_text = normalize_query_text(text)
        if not norm_text or len(norm_text) < 2:
            return
        
        ckey = canonical_key(norm_text)
        if ckey in _EXCLUDED_SHORT_WORDS:
            return
        
        # Deduplicate identical (pattern, label) pairs
        pat_key = f"{label.value}:{ckey}"
        if pat_key in seen_pattern_keys:
            return
        seen_pattern_keys.add(pat_key)

        patterns.append({
            "label": label.value,
            "pattern": norm_text,
            "id": entity_id,
        })

    # 1. Query all Programs and Channels from DB
    programs: List[Program] = db.query(Program).all()

    for p in programs:
        p_name = clean_str(p.name)
        if not p_name:
            continue

        p_key = canonical_key(p_name)
        prog_info = {
            "id": p.id,
            "name": p_name,
            "slug": p.slug,
            "type": p.type,
            "channel_name": p.channel_name,
            "info_genre": p.info_genre,
            "info_language": p.info_language,
        }
        kb.programs_by_key[p_key] = prog_info
        kb.programs_by_id[p.id] = prog_info

        # Add pattern based on entity type (Channel vs Program)
        if p.type == "channel":
            kb.channels_by_key[p_key] = p_name
            add_pattern(p_name, EntityType.CHANNEL, p.id, p_name)
        else:
            add_pattern(p_name, EntityType.PROGRAM_TITLE, p.id, p_name)

        # Add slug alias if readable and distinct
        if p.slug:
            slug_clean = p.slug.replace("-", " ").strip()
            if slug_clean and slug_clean.lower() != p_name.lower():
                target_type = EntityType.CHANNEL if p.type == "channel" else EntityType.PROGRAM_TITLE
                add_pattern(slug_clean, target_type, p.id, p_name)

        # Collect Channel from program attribute
        if p.channel_name:
            c_name = clean_str(p.channel_name)
            if c_name:
                ck = canonical_key(c_name)
                kb.channels_by_key[ck] = c_name
                add_pattern(c_name, EntityType.CHANNEL, c_name, c_name)

        # Collect Genres
        if p.info_genre:
            for g in split_tags(p.info_genre):
                gk = canonical_key(g)
                if gk and gk not in _EXCLUDED_SHORT_WORDS:
                    kb.genres_by_key[gk] = g
                    add_pattern(g, EntityType.GENRE, g, g)

        # Collect Content Types
        if p.info_content_type:
            for ct in split_tags(p.info_content_type):
                ctk = canonical_key(ct)
                if ctk and ctk not in _EXCLUDED_SHORT_WORDS:
                    kb.content_types_by_key[ctk] = ct
                    add_pattern(ct, EntityType.CONTENT_TYPE, ct, ct)

        # Collect Languages
        if p.info_language:
            lang = clean_str(p.info_language)
            if lang:
                lk = canonical_key(lang)
                if lk and lk not in _EXCLUDED_SHORT_WORDS:
                    kb.languages_by_key[lk] = lang.title()
                    add_pattern(lang, EntityType.LANGUAGE, lang.title(), lang.title())

        # Collect Lead Cast / Actors
        if p.info_staring:
            for actor in split_tags(p.info_staring):
                ak = canonical_key(actor)
                if ak and len(actor) >= 3 and ak not in _EXCLUDED_SHORT_WORDS:
                    kb.actors_by_key[ak] = actor
                    add_pattern(actor, EntityType.PERSON, actor, actor)

    # 2. Collect any distinct broadcast channels from episodes table
    from app.models.episode import Episode
    ep_channels = db.query(Episode.channel_name).distinct().filter(Episode.channel_name.isnot(None)).all()
    for (ch,) in ep_channels:
        ch_clean = clean_str(ch)
        if ch_clean:
            chk = canonical_key(ch_clean)
            if chk and chk not in _EXCLUDED_SHORT_WORDS:
                kb.channels_by_key[chk] = ch_clean
                add_pattern(ch_clean, EntityType.CHANNEL, ch_clean, ch_clean)

    # 3. Register Semantic Intent Synonyms (funny -> Comedy, movie -> movie, etc.)
    for entity_type, syn_list, canonical_val in OTT_INTENT_SYNONYMS:
        for syn in syn_list:
            syn_key = canonical_key(syn)
            if entity_type == EntityType.GENRE:
                kb.genres_by_key[syn_key] = canonical_val
            elif entity_type == EntityType.CONTENT_TYPE:
                kb.content_types_by_key[syn_key] = canonical_val
            add_pattern(syn, entity_type, canonical_val, canonical_val)

    # Bound maximum rules for resource safety on 8GB RAM
    kb.patterns = patterns[:max_patterns]
    logger.info(
        f"Grounded CinePulse catalog KB built: {len(kb.patterns)} entity patterns "
        f"({len(kb.programs_by_key)} programs, {len(kb.channels_by_key)} channels, "
        f"{len(kb.genres_by_key)} genres, {len(kb.actors_by_key)} actors)"
    )
    return kb

"""Pydantic schemas and data types for the CinePulse spaCy NLP layer."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    PROGRAM_TITLE = "PROGRAM_TITLE"
    EPISODE_NUMBER = "EPISODE_NUMBER"
    GENRE = "GENRE"
    CHANNEL = "CHANNEL"
    CONTENT_TYPE = "CONTENT_TYPE"
    LANGUAGE = "LANGUAGE"
    PERSON = "PERSON"


class ExtractedEntity(BaseModel):
    """An entity span extracted and resolved by the CinePulse NLP pipeline."""
    text: str = Field(description="Original matching text span in query")
    label: str = Field(description="Entity category label e.g. PROGRAM_TITLE, GENRE")
    start_char: int = Field(description="0-indexed start character offset")
    end_char: int = Field(description="0-indexed end character offset")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    source: str = Field(default="catalog_exact", description="Source: catalog_exact, rule_regex, spacy_ner")
    resolved_id: Optional[str] = Field(default=None, description="Resolved database or catalog ID")
    canonical_name: Optional[str] = Field(default=None, description="Standardized canonical display name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional contextual metadata")


class QueryInterpretation(BaseModel):
    """Structured query understanding object produced by the CinePulse NLP parser."""
    model_config = {"protected_namespaces": ()}

    original_query: str = Field(description="Raw query input from the user")
    normalized_query: str = Field(description="Deterministic normalized query string")
    recognized_entities: List[ExtractedEntity] = Field(default_factory=list, description="Extracted entity spans")
    episode_number: Optional[int] = Field(default=None, description="Explicit parsed episode sequence number")
    matched_program_id: Optional[str] = Field(default=None, description="Resolved canonical program ID if matched")
    matched_program_name: Optional[str] = Field(default=None, description="Canonical program name if matched")
    matched_genre: Optional[str] = Field(default=None, description="Resolved canonical genre filter")
    matched_channel: Optional[str] = Field(default=None, description="Resolved canonical channel filter")
    matched_content_type: Optional[str] = Field(default=None, description="Resolved content type format")
    matched_language: Optional[str] = Field(default=None, description="Resolved language filter")
    remaining_query: str = Field(description="Free-text query remaining after extracting structured entities")
    inferred_filters: Dict[str, Any] = Field(default_factory=dict, description="Safe allowlisted Meilisearch filters")
    is_nlp_assisted: bool = Field(default=False, description="Whether NLP rules or NER successfully enhanced query")
    model_name: Optional[str] = Field(default=None, description="Loaded spaCy pipeline name")
    parser_version: str = Field(default="1.0.0", description="NLP query parser version")
    diagnostics: Dict[str, Any] = Field(default_factory=dict, description="Non-sensitive execution diagnostics")


class NLPServiceStatus(BaseModel):
    """Health and diagnostic readiness status of the shared NLP service."""
    model_config = {"protected_namespaces": ()}

    is_available: bool = Field(description="Whether spaCy model and rule-engine are loaded and ready")
    model_name: Optional[str] = Field(default=None, description="spaCy model package name")
    spacy_version: Optional[str] = Field(default=None, description="Installed spaCy library version")
    patterns_loaded: int = Field(default=0, description="Total verified catalog entity patterns registered")
    pipeline_components: List[str] = Field(default_factory=list, description="Active spaCy pipeline components")
    last_initialized_at: Optional[str] = Field(default=None, description="ISO timestamp of last initialization")
    device: str = Field(default="cpu", description="Execution target device (strictly CPU for 8GB RAM)")

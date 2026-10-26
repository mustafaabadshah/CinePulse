"""Thread-safe NLP Service managing the shared spaCy pipeline and catalog entity ruler."""

from __future__ import annotations

from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional
import spacy
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import logger
from app.services.nlp.catalog_entities import CatalogKnowledgeBase, build_catalog_knowledge_base
from app.services.nlp.normalization import normalize_query_text
from app.services.nlp.query_parser import QueryParser
from app.services.nlp.schemas import NLPServiceStatus, QueryInterpretation


class NLPService:
    """Manages the shared spaCy pipeline, catalog knowledge base, and query parsing."""

    def __init__(self):
        self._lock = threading.Lock()
        self._nlp: Optional[spacy.language.Language] = None
        self._kb: Optional[CatalogKnowledgeBase] = None
        self._parser: Optional[QueryParser] = None
        self._is_ready: bool = False
        self._model_name: Optional[str] = None
        self._spacy_version: Optional[str] = None
        self._pipeline_components: List[str] = []
        self._initialized_at: Optional[str] = None
        self._init_error: Optional[str] = None

    @property
    def is_ready(self) -> bool:
        return self._is_ready and self._parser is not None

    def initialize(self, db: Session, force_reload: bool = False) -> None:
        """Initializes the spaCy pipeline and entity ruler with catalog entities.
        
        Designed to be called once during application startup (FastAPI lifespan).
        Resource constraints: strictly runs on CPU with lightweight memory footprint.
        """
        with self._lock:
            if self._is_ready and not force_reload:
                logger.info("NLPService is already initialized and ready.")
                return

            if not getattr(settings, "nlp_enabled", True):
                logger.info("NLP processing is disabled via settings (nlp_enabled=False).")
                self._is_ready = False
                return

            model_name = getattr(settings, "spacy_model", "en_core_web_sm")
            logger.info(f"Initializing CinePulse NLP service with model '{model_name}'...")

            try:
                # 1. Load spaCy model (disable heavyweight parser/lemmatizer if not needed to conserve memory)
                # We retain 'tagger', 'attribute_ruler' and optionally 'ner'
                try:
                    nlp = spacy.load(model_name, disable=["lemmatizer"])
                except Exception as load_err:
                    logger.warning(
                        f"Could not load spaCy model '{model_name}': {load_err}. "
                        "Falling back to spacy.blank('en')."
                    )
                    nlp = spacy.blank("en")

                # 2. Build grounded catalog knowledge base from database
                kb = build_catalog_knowledge_base(db)

                # 3. Add EntityRuler component configured with LOWER phrase matching
                if "entity_ruler" in nlp.pipe_names:
                    nlp.remove_pipe("entity_ruler")

                ruler_kwargs = {"phrase_matcher_attr": "LOWER", "overwrite_ents": True}
                if "ner" in nlp.pipe_names:
                    ruler = nlp.add_pipe("entity_ruler", before="ner", config=ruler_kwargs)
                else:
                    ruler = nlp.add_pipe("entity_ruler", config=ruler_kwargs)

                # 4. Add patterns in bulk
                ruler.add_patterns(kb.patterns)

                # 5. Build parser
                confidence_threshold = getattr(settings, "nlp_confidence_threshold", 0.6)
                max_query_length = getattr(settings, "nlp_max_query_length", 200)

                self._nlp = nlp
                self._kb = kb
                self._parser = QueryParser(
                    nlp=nlp,
                    kb=kb,
                    confidence_threshold=confidence_threshold,
                    max_query_length=max_query_length,
                )
                self._model_name = model_name
                self._spacy_version = spacy.__version__
                self._pipeline_components = list(nlp.pipe_names)
                self._initialized_at = datetime.now(timezone.utc).isoformat()
                self._is_ready = True
                self._init_error = None

                logger.info(
                    f"CinePulse NLPService initialized successfully. "
                    f"spaCy v{self._spacy_version}, pipes: {self._pipeline_components}, "
                    f"patterns: {kb.total_patterns}"
                )

            except Exception as exc:
                self._is_ready = False
                self._init_error = str(exc)
                logger.exception(f"Failed to initialize NLPService: {exc}")

    def parse_query(self, query: str) -> QueryInterpretation:
        """Parses a query into structured interpretations.
        
        Guaranteed to be non-blocking and safe: returns a clean baseline interpretation
        if the NLP pipeline is uninitialized, disabled, or encounters an issue.
        """
        if not self._is_ready or self._parser is None:
            norm = normalize_query_text(query)
            return QueryInterpretation(
                original_query=query or "",
                normalized_query=norm,
                remaining_query=norm,
                is_nlp_assisted=False,
                diagnostics={"status": "nlp_not_initialized", "error": self._init_error},
            )

        try:
            return self._parser.parse(query)
        except Exception as exc:
            logger.warning(f"Unexpected error during query parsing for '{query}': {exc}")
            norm = normalize_query_text(query)
            return QueryInterpretation(
                original_query=query or "",
                normalized_query=norm,
                remaining_query=norm,
                is_nlp_assisted=False,
                diagnostics={"error": str(exc)},
            )

    def get_status(self) -> NLPServiceStatus:
        """Returns the readiness and diagnostic telemetry of the NLP service."""
        return NLPServiceStatus(
            is_available=self._is_ready,
            model_name=self._model_name,
            spacy_version=self._spacy_version,
            patterns_loaded=self._kb.total_patterns if self._kb else 0,
            pipeline_components=self._pipeline_components,
            last_initialized_at=self._initialized_at,
            device="cpu",
        )


# Global singleton instance for application use
nlp_service = NLPService()

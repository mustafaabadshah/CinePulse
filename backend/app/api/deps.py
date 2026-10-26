"""FastAPI dependencies for DB sessions and search services."""

from app.core.database import get_db
from app.search.service import SearchService
from app.services.nlp.service import NLPService, nlp_service
from fastapi import Depends
from sqlalchemy.orm import Session


def get_nlp_service() -> NLPService:
    """Dependency for obtaining the shared NLPService singleton."""
    return nlp_service


def get_search_service(
    db: Session = Depends(get_db),
    nlp: NLPService = Depends(get_nlp_service),
) -> SearchService:
    """Dependency for obtaining a SearchService instance."""
    return SearchService(db=db, nlp_service=nlp)


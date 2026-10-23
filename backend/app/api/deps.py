"""FastAPI dependencies for DB sessions and search services."""

from app.core.database import get_db
from app.search.service import SearchService
from fastapi import Depends
from sqlalchemy.orm import Session


def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    """Dependency for obtaining a SearchService instance."""
    return SearchService(db=db)

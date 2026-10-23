"""System health and diagnostic endpoints."""

from app.core.database import get_db
from app.search.client import check_meili_health, get_meili_client
from app.search.indexes import INDEX_INSTITUTIONS, INDEX_PUBLICATIONS, INDEX_RESEARCHERS
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    """Health check validating backend, database connectivity, and Meilisearch engine status."""
    # Check DB
    db_healthy = False
    try:
        db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception:
        db_healthy = False

    # Check Meilisearch
    meili_healthy = check_meili_health()

    index_stats = {}
    if meili_healthy:
        try:
            client = get_meili_client()
            for idx in [INDEX_RESEARCHERS, INDEX_PUBLICATIONS, INDEX_INSTITUTIONS]:
                try:
                    stats = client.index(idx).get_stats()
                    index_stats[idx] = {
                        "number_of_documents": stats.number_of_documents,
                        "is_indexing": stats.is_indexing,
                    }
                except Exception:
                    index_stats[idx] = {"status": "unavailable"}
        except Exception:
            pass

    overall_healthy = db_healthy and meili_healthy

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "components": {
            "database": {
                "status": "up" if db_healthy else "down",
            },
            "meilisearch": {
                "status": "up" if meili_healthy else "down",
                "indexes": index_stats,
            },
        },
    }

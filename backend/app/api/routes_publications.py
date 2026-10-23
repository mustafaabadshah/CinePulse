"""Publication retrieval endpoints."""

from typing import List, Optional

from app.core.database import get_db
from app.models import Institution, Publication, SourceRecord
from app.schemas.publication import PublicationRead
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/publications", tags=["Publications"])


@router.get("", response_model=List[PublicationRead])
def list_publications(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    year: Optional[int] = Query(default=None),
    venue: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[PublicationRead]:
    """Retrieves paginated publications from relational database."""
    query = db.query(Publication)
    if year:
        query = query.filter(Publication.publication_year == year)
    if venue:
        query = query.filter(Publication.venue == venue)

    return query.offset(offset).limit(limit).all()


@router.get("/{id}")
def get_publication(id: str, db: Session = Depends(get_db)):
    """Retrieves complete details for a publication including provenance and primary institution."""
    pub = db.query(Publication).filter(Publication.id == id).first()
    if not pub:
        raise HTTPException(status_code=404, detail=f"Publication '{id}' not found.")

    provenance = (
        db.query(SourceRecord)
        .filter(SourceRecord.entity_type == "publication", SourceRecord.entity_id == id)
        .first()
    )

    institution = None
    if pub.primary_institution_id:
        institution = (
            db.query(Institution).filter(Institution.id == pub.primary_institution_id).first()
        )

    return {
        "publication": {
            "id": pub.id,
            "title": pub.title,
            "abstract": pub.abstract,
            "authors": pub.authors,
            "primary_institution_id": pub.primary_institution_id,
            "institution_name": institution.name if institution else None,
            "publication_year": pub.publication_year,
            "venue": pub.venue,
            "doi": pub.doi,
            "canonical_url": pub.canonical_url,
            "keywords": pub.keywords,
            "source_provider": pub.source_provider,
            "is_synthetic": pub.is_synthetic,
            "imported_at": pub.imported_at,
            "created_at": pub.created_at,
            "updated_at": pub.updated_at,
        },
        "institution": {
            "id": institution.id,
            "name": institution.name,
            "country": institution.country,
            "city": institution.city,
            "website_url": institution.website_url,
        }
        if institution
        else None,
        "provenance": {
            "source_provider": provenance.source_provider if provenance else pub.source_provider,
            "source_url": provenance.source_url if provenance else (pub.canonical_url or pub.doi),
            "is_verified": provenance.is_verified if provenance else not pub.is_synthetic,
            "imported_at": provenance.imported_at if provenance else pub.imported_at,
        }
        if provenance
        else None,
    }

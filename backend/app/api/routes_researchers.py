"""Researcher retrieval endpoints."""

from typing import List, Optional

from app.core.database import get_db
from app.models import Institution, Publication, Researcher, SourceRecord
from app.schemas.researcher import ResearcherRead
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/researchers", tags=["Researchers"])


@router.get("", response_model=List[ResearcherRead])
def list_researchers(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    country: Optional[str] = Query(default=None),
    institution_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[ResearcherRead]:
    """Retrieves paginated researchers from relational storage."""
    query = db.query(Researcher)
    if country:
        query = query.filter(Researcher.country == country)
    if institution_id:
        query = query.filter(Researcher.institution_id == institution_id)

    results = query.offset(offset).limit(limit).all()
    # Enrich with institution name
    output = []
    for r in results:
        read_obj = ResearcherRead.model_validate(r)
        if r.institution:
            read_obj.institution_name = r.institution.name
        output.append(read_obj)
    return output


@router.get("/{id}")
def get_researcher(id: str, db: Session = Depends(get_db)):
    """Retrieves detailed record for a researcher including institutional profile and provenance."""
    researcher = db.query(Researcher).filter(Researcher.id == id).first()
    if not researcher:
        raise HTTPException(status_code=404, detail=f"Researcher '{id}' not found.")

    provenance = (
        db.query(SourceRecord)
        .filter(SourceRecord.entity_type == "researcher", SourceRecord.entity_id == id)
        .first()
    )

    institution = db.query(Institution).filter(Institution.id == researcher.institution_id).first()

    # Find publications where researcher name is among authors
    publications = (
        db.query(Publication)
        .filter(Publication.authors.contains(researcher.full_name))
        .limit(10)
        .all()
    )

    return {
        "researcher": {
            "id": researcher.id,
            "full_name": researcher.full_name,
            "official_profile_url": researcher.official_profile_url,
            "institution_id": researcher.institution_id,
            "institution_name": institution.name if institution else None,
            "department": researcher.department,
            "country": researcher.country,
            "research_interests": researcher.research_interests,
            "biography": researcher.biography,
            "contact_email_verified": researcher.contact_email_verified,
            "contact_email": researcher.contact_email,
            "contact_source_url": researcher.contact_source_url,
            "last_verified_at": researcher.last_verified_at,
            "is_synthetic": researcher.is_synthetic,
            "created_at": researcher.created_at,
            "updated_at": researcher.updated_at,
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
            "source_provider": provenance.source_provider if provenance else "unknown",
            "source_url": provenance.source_url if provenance else None,
            "is_verified": provenance.is_verified if provenance else False,
            "imported_at": provenance.imported_at if provenance else None,
        }
        if provenance
        else None,
        "publications": [
            {
                "id": p.id,
                "title": p.title,
                "publication_year": p.publication_year,
                "venue": p.venue,
                "doi": p.doi,
            }
            for p in publications
        ],
    }

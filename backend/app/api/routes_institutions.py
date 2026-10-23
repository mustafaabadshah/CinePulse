"""Institution retrieval endpoints."""

from typing import List, Optional

from app.core.database import get_db
from app.models import Institution, Publication, Researcher, SourceRecord
from app.schemas.institution import InstitutionRead
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.get("", response_model=List[InstitutionRead])
def list_institutions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    country: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[InstitutionRead]:
    """Retrieves paginated institutions."""
    query = db.query(Institution)
    if country:
        query = query.filter(Institution.country == country)
    return query.offset(offset).limit(limit).all()


@router.get("/{id}")
def get_institution(id: str, db: Session = Depends(get_db)):
    """Retrieves detailed record for an institution including affiliated faculty and publications."""
    inst = db.query(Institution).filter(Institution.id == id).first()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Institution '{id}' not found.")

    provenance = (
        db.query(SourceRecord)
        .filter(SourceRecord.entity_type == "institution", SourceRecord.entity_id == id)
        .first()
    )

    researchers = db.query(Researcher).filter(Researcher.institution_id == id).all()
    publications = db.query(Publication).filter(Publication.primary_institution_id == id).all()

    return {
        "institution": {
            "id": inst.id,
            "name": inst.name,
            "normalized_name": inst.normalized_name,
            "country": inst.country,
            "city": inst.city,
            "website_url": inst.website_url,
            "ror_id": inst.ror_id,
            "created_at": inst.created_at,
            "updated_at": inst.updated_at,
        },
        "provenance": {
            "source_provider": provenance.source_provider if provenance else "unknown",
            "source_url": provenance.source_url if provenance else inst.website_url,
            "is_verified": provenance.is_verified if provenance else bool(inst.ror_id),
            "imported_at": provenance.imported_at if provenance else inst.created_at,
        }
        if provenance
        else None,
        "faculty_count": len(researchers),
        "researchers": [
            {
                "id": r.id,
                "full_name": r.full_name,
                "department": r.department,
                "research_interests": r.research_interests,
            }
            for r in researchers
        ],
        "publications_count": len(publications),
        "publications": [
            {
                "id": p.id,
                "title": p.title,
                "publication_year": p.publication_year,
                "venue": p.venue,
            }
            for p in publications
        ],
    }

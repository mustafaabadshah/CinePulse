"""API endpoints for CinePulse spaCy NLP status and query interpretation debugging."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_nlp_service
from app.services.nlp.schemas import NLPServiceStatus, QueryInterpretation
from app.services.nlp.service import NLPService

router = APIRouter(prefix="/nlp", tags=["NLP & Entity Recognition"])


class ParseQueryRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=300, description="Query text to parse and ground")


@router.get("/status", response_model=NLPServiceStatus)
def get_nlp_status(nlp: NLPService = Depends(get_nlp_service)) -> NLPServiceStatus:
    """Returns the operational status, loaded spaCy model, and registered catalog patterns."""
    return nlp.get_status()


@router.post("/parse", response_model=QueryInterpretation)
def parse_query_endpoint(
    req: ParseQueryRequest,
    nlp: NLPService = Depends(get_nlp_service),
) -> QueryInterpretation:
    """Parses a search query using spaCy NER and catalog grounding without executing a search."""
    return nlp.parse_query(req.q)

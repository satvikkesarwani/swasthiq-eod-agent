from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_narrative_provider
from app.integrations.llm_provider import NarrativeProvider
from app.schemas.report import ErrorResponse
from app.schemas.narrative import NarrativeGenerateRequest, NarrativeResponse
from app.services.narrative_service import NarrativeService

router = APIRouter(prefix="/clinic-days", tags=["narratives"])

ERROR_RESPONSES = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


@router.post("/{clinic_id}/{business_date}/narrative", response_model=NarrativeResponse, responses=ERROR_RESPONSES)
async def generate_narrative(
    clinic_id: str,
    business_date: date,
    payload: NarrativeGenerateRequest,
    session: Session = Depends(get_db),
    provider: NarrativeProvider = Depends(get_narrative_provider),
) -> NarrativeResponse:
    return await NarrativeService(session, provider).generate(
        clinic_id=clinic_id,
        business_date=business_date,
        force_regenerate=payload.force_regenerate,
    )


@router.get("/{clinic_id}/{business_date}/narrative", response_model=NarrativeResponse, responses=ERROR_RESPONSES)
def get_narrative(
    clinic_id: str,
    business_date: date,
    session: Session = Depends(get_db),
    provider: NarrativeProvider = Depends(get_narrative_provider),
) -> NarrativeResponse:
    return NarrativeService(session, provider).get(clinic_id=clinic_id, business_date=business_date)

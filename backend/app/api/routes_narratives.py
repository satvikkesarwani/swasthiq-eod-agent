from datetime import date

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_narrative_provider
from app.integrations.llm_provider import NarrativeProvider
from app.schemas.report import ErrorResponse
from app.schemas.narrative import NarrativeGenerateRequest, NarrativeResponse
from app.services.narrative_service import NarrativeService
from app.core.rate_limit import raise_rate_limited

router = APIRouter(prefix="/clinic-days", tags=["narratives"])
logger = logging.getLogger(__name__)

ERROR_RESPONSES = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


@router.post("/{clinic_id}/{business_date}/narrative", response_model=NarrativeResponse, responses=ERROR_RESPONSES)
async def generate_narrative(
    clinic_id: str,
    business_date: date,
    payload: NarrativeGenerateRequest,
    request: Request,
    session: Session = Depends(get_db),
    provider: NarrativeProvider = Depends(get_narrative_provider),
) -> NarrativeResponse:
    limiter = request.app.state.narrative_rate_limiter
    retry_after = limiter.check(f"{clinic_id}:{business_date.isoformat()}")
    if retry_after is not None:
        logger.warning("narrative.rate_limited clinic_id=%s business_date=%s retry_after=%s", clinic_id, business_date, retry_after)
        raise_rate_limited(retry_after)
    logger.info("narrative.route.generate start clinic_id=%s business_date=%s force=%s", clinic_id, business_date, payload.force_regenerate)
    response = await NarrativeService(session, provider).generate(
        clinic_id=clinic_id,
        business_date=business_date,
        force_regenerate=payload.force_regenerate,
    )
    logger.info(
        "narrative.route.generate done clinic_id=%s business_date=%s status=%s traces=%s fallback_reason=%s",
        clinic_id,
        business_date,
        response.status,
        len(response.traces),
        response.fallback_reason_code,
    )
    return response


@router.get("/{clinic_id}/{business_date}/narrative", response_model=NarrativeResponse, responses=ERROR_RESPONSES)
def get_narrative(
    clinic_id: str,
    business_date: date,
    session: Session = Depends(get_db),
    provider: NarrativeProvider = Depends(get_narrative_provider),
) -> NarrativeResponse:
    return NarrativeService(session, provider).get(clinic_id=clinic_id, business_date=business_date)

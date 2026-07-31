from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.serializers import serialize_clinic_day, serialize_ingestion_issues, serialize_list_item
from app.core.errors import AppError
from app.repositories.clinic_day_repository import ClinicDayRepository
from app.schemas.ingestion import BillingLogRequest
from app.schemas.report import ClinicDayListResponse, ClinicDayResponse, ErrorResponse, IngestionIssueListResponse
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/clinic-days", tags=["clinic-days"])


ERROR_RESPONSES = {
    404: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


@router.get("", response_model=ClinicDayListResponse, responses=ERROR_RESPONSES)
def list_clinic_days(
    clinic_id: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
) -> ClinicDayListResponse:
    items = ClinicDayRepository(session).list_all(
        clinic_id=clinic_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return ClinicDayListResponse(items=[serialize_list_item(item) for item in items], limit=limit, offset=offset, count=len(items))


@router.put("/{clinic_id}/{business_date}", response_model=ClinicDayResponse, responses=ERROR_RESPONSES)
def replace_clinic_day(
    clinic_id: str,
    business_date: date,
    payload: BillingLogRequest,
    http_request: Request,
    session: Session = Depends(get_db),
) -> ClinicDayResponse:
    settings = http_request.app.state.settings
    clinic_day, operation = IngestionService(
        session,
        max_records=settings.max_records_per_request,
        store_rejected_raw_rows=settings.store_rejected_raw_rows,
    ).replace_clinic_day(
        clinic_id=clinic_id,
        business_date=business_date,
        request=payload,
    )
    return serialize_clinic_day(clinic_day, operation=operation)


@router.get("/{clinic_id}/{business_date}", response_model=ClinicDayResponse, responses=ERROR_RESPONSES)
def get_clinic_day(
    clinic_id: str, business_date: date, session: Session = Depends(get_db)
) -> ClinicDayResponse:
    clinic_day = ClinicDayRepository(session).get(clinic_id, business_date, with_children=True)
    if clinic_day is None:
        raise AppError(code="CLINIC_DAY_NOT_FOUND", message="Clinic-day report was not found.", status_code=404)
    return serialize_clinic_day(clinic_day)


@router.get("/{clinic_id}/{business_date}/errors", response_model=IngestionIssueListResponse, responses=ERROR_RESPONSES)
def get_ingestion_errors(
    clinic_id: str,
    business_date: date,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
) -> IngestionIssueListResponse:
    clinic_day = ClinicDayRepository(session).get(clinic_id, business_date, with_children=True)
    if clinic_day is None:
        raise AppError(code="CLINIC_DAY_NOT_FOUND", message="Clinic-day report was not found.", status_code=404)
    errors = serialize_ingestion_issues(clinic_day)
    paged = errors[offset:offset + limit]
    return IngestionIssueListResponse(
        clinic_id=clinic_id,
        business_date=business_date,
        count=len(paged),
        limit=limit,
        offset=offset,
        errors=paged,
    )

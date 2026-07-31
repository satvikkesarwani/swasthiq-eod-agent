import logging
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
logger = logging.getLogger(__name__)


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
    logger.info(
        "clinic_days.list start clinic_id=%s date_from=%s date_to=%s limit=%s offset=%s",
        clinic_id,
        date_from,
        date_to,
        limit,
        offset,
    )
    items = ClinicDayRepository(session).list_all(
        clinic_id=clinic_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    logger.info("clinic_days.list success count=%s", len(items))
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
    logger.info(
        "clinic_days.replace start request_id=%s clinic_id=%s business_date=%s records=%s clinic_name_present=%s clinic_location_present=%s",
        getattr(http_request.state, "request_id", None),
        clinic_id,
        business_date,
        len(payload.records),
        payload.clinic_name is not None,
        payload.clinic_location is not None,
    )
    clinic_day, operation = IngestionService(
        session,
        max_records=settings.max_records_per_request,
        store_rejected_raw_rows=settings.store_rejected_raw_rows,
    ).replace_clinic_day(
        clinic_id=clinic_id,
        business_date=business_date,
        request=payload,
    )
    logger.info(
        "clinic_days.replace success request_id=%s clinic_id=%s business_date=%s operation=%s status=%s accepted=%s rejected=%s",
        getattr(http_request.state, "request_id", None),
        clinic_id,
        business_date,
        operation,
        clinic_day.status,
        clinic_day.accepted_rows,
        clinic_day.rejected_rows,
    )
    return serialize_clinic_day(clinic_day, operation=operation)


@router.get("/{clinic_id}/{business_date}", response_model=ClinicDayResponse, responses=ERROR_RESPONSES)
def get_clinic_day(
    clinic_id: str, business_date: date, session: Session = Depends(get_db)
) -> ClinicDayResponse:
    logger.info("clinic_days.get start clinic_id=%s business_date=%s", clinic_id, business_date)
    clinic_day = ClinicDayRepository(session).get(clinic_id, business_date, with_children=True)
    if clinic_day is None:
        logger.warning("clinic_days.get not_found clinic_id=%s business_date=%s", clinic_id, business_date)
        raise AppError(code="CLINIC_DAY_NOT_FOUND", message="Clinic-day report was not found.", status_code=404)
    logger.info("clinic_days.get success clinic_id=%s business_date=%s status=%s", clinic_id, business_date, clinic_day.status)
    return serialize_clinic_day(clinic_day)


@router.get("/{clinic_id}/{business_date}/errors", response_model=IngestionIssueListResponse, responses=ERROR_RESPONSES)
def get_ingestion_errors(
    clinic_id: str,
    business_date: date,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db),
) -> IngestionIssueListResponse:
    logger.info(
        "clinic_days.errors start clinic_id=%s business_date=%s limit=%s offset=%s",
        clinic_id,
        business_date,
        limit,
        offset,
    )
    clinic_day = ClinicDayRepository(session).get(clinic_id, business_date, with_children=True)
    if clinic_day is None:
        logger.warning("clinic_days.errors not_found clinic_id=%s business_date=%s", clinic_id, business_date)
        raise AppError(code="CLINIC_DAY_NOT_FOUND", message="Clinic-day report was not found.", status_code=404)
    errors = serialize_ingestion_issues(clinic_day)
    paged = errors[offset:offset + limit]
    logger.info("clinic_days.errors success clinic_id=%s business_date=%s count=%s", clinic_id, business_date, len(paged))
    return IngestionIssueListResponse(
        clinic_id=clinic_id,
        business_date=business_date,
        count=len(paged),
        limit=limit,
        offset=offset,
        errors=paged,
    )

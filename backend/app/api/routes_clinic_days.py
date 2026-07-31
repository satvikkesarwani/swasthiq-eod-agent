from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.serializers import serialize_clinic_day, serialize_list_item
from app.core.errors import AppError
from app.repositories.clinic_day_repository import ClinicDayRepository
from app.schemas.ingestion import BillingLogRequest
from app.schemas.report import ClinicDayListResponse, ClinicDayResponse
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/clinic-days", tags=["clinic-days"])


@router.get("", response_model=ClinicDayListResponse)
def list_clinic_days(
    clinic_id: str | None = Query(default=None), session: Session = Depends(get_db)
) -> ClinicDayListResponse:
    items = ClinicDayRepository(session).list_all(clinic_id)
    return ClinicDayListResponse(items=[serialize_list_item(item) for item in items])


@router.put("/{clinic_id}/{business_date}", response_model=ClinicDayResponse)
def replace_clinic_day(
    clinic_id: str,
    business_date: date,
    payload: BillingLogRequest,
    response: Response,
    http_request: Request,
    session: Session = Depends(get_db),
) -> ClinicDayResponse:
    settings = http_request.app.state.settings
    clinic_day, created = IngestionService(
        session,
        max_records=settings.max_records_per_request,
        store_rejected_raw_rows=settings.store_rejected_raw_rows,
    ).replace_clinic_day(
        clinic_id=clinic_id,
        business_date=business_date,
        request=payload,
    )
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return serialize_clinic_day(clinic_day)


@router.get("/{clinic_id}/{business_date}", response_model=ClinicDayResponse)
def get_clinic_day(
    clinic_id: str, business_date: date, session: Session = Depends(get_db)
) -> ClinicDayResponse:
    clinic_day = ClinicDayRepository(session).get(clinic_id, business_date, with_children=True)
    if clinic_day is None:
        raise AppError(code="CLINIC_DAY_NOT_FOUND", message="Clinic-day report was not found.", status_code=404)
    return serialize_clinic_day(clinic_day)


@router.get("/{clinic_id}/{business_date}/errors")
def get_ingestion_errors(clinic_id: str, business_date: date, session: Session = Depends(get_db)) -> dict:
    clinic_day = ClinicDayRepository(session).get(clinic_id, business_date, with_children=True)
    if clinic_day is None:
        raise AppError(code="CLINIC_DAY_NOT_FOUND", message="Clinic-day report was not found.", status_code=404)
    errors = serialize_clinic_day(clinic_day).ingestion.errors
    return {"clinic_id": clinic_id, "business_date": business_date, "count": len(errors), "errors": errors}

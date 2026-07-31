import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.serializers import serialize_clinic_day, serialize_ingestion_issues, serialize_list_item
from app.core.limits import MAX_CLINIC_ID_LENGTH
from app.core.errors import AppError
from app.core.safe_strings import clean_user_string, safe_error_code, safe_error_message, safe_field_path
from app.core.strict_json import decode_strict_json_body
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


def parse_business_date(value: str) -> date:
    if not isinstance(value, str):
        raise AppError(code="INVALID_FIELD_TYPE", message="Business date must be YYYY-MM-DD.", status_code=422)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise AppError(code="INVALID_IDENTIFIER", message="Business date must be a valid YYYY-MM-DD date.", status_code=422) from exc
    if parsed.isoformat() != value:
        raise AppError(code="INVALID_IDENTIFIER", message="Business date must be a valid YYYY-MM-DD date.", status_code=422)
    return parsed


async def parse_billing_log_request(request: Request) -> BillingLogRequest:
    settings = request.app.state.settings
    decoded = decode_strict_json_body(
        await request.body(),
        max_depth=settings.max_json_depth,
        max_nodes=settings.max_json_nodes,
    )
    if not isinstance(decoded, dict):
        raise AppError(code="INVALID_JSON", message="Import request must be a JSON object.", status_code=422)
    try:
        payload = BillingLogRequest.model_validate(decoded)
    except ValidationError as exc:
        details = [
            {
                "field": safe_field_path(".".join(str(part) for part in error["loc"])),
                "code": safe_error_code("INVALID_FIELD_TYPE" if error["type"].startswith(("int_", "bool_", "string_type", "datetime_")) else error["type"]),
                "message": safe_error_message(error["msg"]),
            }
            for error in exc.errors(include_url=False)[: settings.max_issues_per_request]
        ]
        raise AppError(code="INVALID_FIELD_TYPE", message="Import request fields could not be validated.", status_code=422, details=details) from exc
    return payload


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


@router.put(
    "/{clinic_id}/{business_date}",
    response_model=ClinicDayResponse,
    responses=ERROR_RESPONSES,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/BillingLogRequest"}
                }
            },
        }
    },
)
def replace_clinic_day(
    clinic_id: str,
    business_date: str,
    http_request: Request,
    payload: BillingLogRequest = Depends(parse_billing_log_request),
    session: Session = Depends(get_db),
) -> ClinicDayResponse:
    settings = http_request.app.state.settings
    parsed_clinic_id = clean_user_string(clinic_id, field="clinic_id", max_length=MAX_CLINIC_ID_LENGTH)
    parsed_business_date = parse_business_date(business_date)
    logger.info(
        "clinic_days.replace start request_id=%s clinic_id=%s business_date=%s records=%s clinic_name_present=%s clinic_location_present=%s",
        getattr(http_request.state, "request_id", None),
        parsed_clinic_id,
        parsed_business_date,
        len(payload.records),
        payload.clinic_name is not None,
        payload.clinic_location is not None,
    )
    clinic_day, operation = IngestionService(
        session,
        max_records=settings.max_records_per_request,
        max_line_items=settings.max_line_items_per_record,
        max_issues_per_row=settings.max_issues_per_row,
        max_issues_per_request=settings.max_issues_per_request,
        max_persisted_issues=settings.max_persisted_issues_per_report,
        max_medicine_warnings=settings.max_medicine_warnings_per_report,
        max_medicine_comparisons=settings.max_medicine_comparisons_per_report,
        max_safe_paise=settings.max_safe_paise,
        store_rejected_raw_rows=settings.store_rejected_raw_rows,
    ).replace_clinic_day(
        clinic_id=parsed_clinic_id,
        business_date=parsed_business_date,
        request=payload,
    )
    logger.info(
        "clinic_days.replace success request_id=%s clinic_id=%s business_date=%s operation=%s status=%s accepted=%s rejected=%s",
        getattr(http_request.state, "request_id", None),
        parsed_clinic_id,
        parsed_business_date,
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

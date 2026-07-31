from app.models import ClinicDay
from app.schemas.report import (
    ClinicDayListItem,
    ClinicDayResponse,
    DeterministicReport,
    IngestionSummary,
)


def narrative_status(clinic_day: ClinicDay) -> str:
    if clinic_day.narrative is None:
        return "not_generated"
    if clinic_day.narrative.report_hash != clinic_day.report_hash:
        return "stale"
    return clinic_day.narrative.status


def serialize_clinic_day(clinic_day: ClinicDay, *, include_errors: bool = True) -> ClinicDayResponse:
    errors = []
    if include_errors:
        errors = [
            {
                "row_index": error.row_index,
                "visit_id": error.visit_id,
                "field": error.field_path,
                "code": error.code,
                "message": error.message,
            }
            for error in sorted(clinic_day.ingestion_errors, key=lambda item: (item.row_index, item.field_path))
        ]
    return ClinicDayResponse(
        clinic_id=clinic_day.clinic_id,
        clinic_name=clinic_day.clinic_name,
        clinic_location=clinic_day.clinic_location,
        business_date=clinic_day.business_date,
        status=clinic_day.status,
        ingestion=IngestionSummary(
            received_rows=clinic_day.received_rows,
            accepted_rows=clinic_day.accepted_rows,
            rejected_rows=clinic_day.rejected_rows,
            errors=errors,
        ),
        report=DeterministicReport.model_validate(clinic_day.report_json),
        source_hash=clinic_day.source_hash,
        report_hash=clinic_day.report_hash,
        narrative_status=narrative_status(clinic_day),
        created_at=clinic_day.created_at,
        updated_at=clinic_day.updated_at,
    )


def serialize_list_item(clinic_day: ClinicDay) -> ClinicDayListItem:
    return ClinicDayListItem(
        clinic_id=clinic_day.clinic_id,
        clinic_name=clinic_day.clinic_name,
        business_date=clinic_day.business_date,
        status=clinic_day.status,
        accepted_rows=clinic_day.accepted_rows,
        rejected_rows=clinic_day.rejected_rows,
        narrative_status=narrative_status(clinic_day),
        updated_at=clinic_day.updated_at,
    )

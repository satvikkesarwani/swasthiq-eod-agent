from app.models import ClinicDay
from app.schemas.report import (
    ClinicDayListItem,
    ClinicDayResponse,
    DeterministicReport,
    IngestionIssue,
    IngestionSummary,
)
from app.core.money import collection_rate_basis_points


def narrative_status(clinic_day: ClinicDay) -> str:
    if clinic_day.narrative is None:
        return "not_generated"
    if clinic_day.narrative.report_hash != clinic_day.report_hash:
        return "stale"
    return clinic_day.narrative.status


def serialize_ingestion_issues(clinic_day: ClinicDay) -> list[IngestionIssue]:
    return [
        IngestionIssue(
            row_index=error.row_index,
            visit_id=error.visit_id,
            field_path=error.field_path,
            error_code=error.error_code,
            message=error.message,
        )
        for error in sorted(clinic_day.ingestion_errors, key=lambda item: (item.row_index, item.field_path or ""))
    ]


def serialize_clinic_day(
    clinic_day: ClinicDay, *, include_errors: bool = True, operation: str | None = None
) -> ClinicDayResponse:
    errors = []
    if include_errors:
        errors = [issue.model_dump(mode="json") for issue in serialize_ingestion_issues(clinic_day)]
    report_json = _report_json_with_defaults(clinic_day.report_json)
    return ClinicDayResponse(
        clinic_id=clinic_day.clinic_id,
        clinic_name=clinic_day.clinic_name,
        clinic_location=clinic_day.clinic_location,
        business_date=clinic_day.business_date,
        operation=operation,
        status=clinic_day.status,
        ingestion=IngestionSummary(
            received_rows=clinic_day.received_rows,
            accepted_rows=clinic_day.accepted_rows,
            rejected_rows=clinic_day.rejected_rows,
            total_issue_count=getattr(clinic_day, "total_issue_count", len(errors)),
            returned_issue_count=getattr(clinic_day, "returned_issue_count", len(errors)),
            issues_truncated=getattr(clinic_day, "issues_truncated", False),
            errors=errors,
        ),
        report=DeterministicReport.model_validate(report_json),
        source_hash=clinic_day.source_hash,
        report_hash=clinic_day.report_hash,
        narrative_status=narrative_status(clinic_day),
        created_at=clinic_day.created_at,
        updated_at=clinic_day.updated_at,
    )


def serialize_list_item(clinic_day: ClinicDay) -> ClinicDayListItem:
    report_json = _report_json_with_defaults(clinic_day.report_json)
    reconciliation = report_json["reconciliation"]
    return ClinicDayListItem(
        clinic_id=clinic_day.clinic_id,
        clinic_name=clinic_day.clinic_name,
        business_date=clinic_day.business_date,
        status=clinic_day.status,
        accepted_rows=clinic_day.accepted_rows,
        rejected_rows=clinic_day.rejected_rows,
        total_billed_paise=reconciliation["total_billed_paise"],
        total_collected_paise=reconciliation["total_collected_paise"],
        total_outstanding_paise=reconciliation["total_outstanding_paise"],
        total_refunds_paise=reconciliation["total_refunds_paise"],
        report_hash=clinic_day.report_hash,
        narrative_status=narrative_status(clinic_day),
        updated_at=clinic_day.updated_at,
    )


def _report_json_with_defaults(report_json: dict) -> dict:
    report = dict(report_json)
    reconciliation = dict(report.get("reconciliation", {}))
    if "collection_rate_basis_points" not in reconciliation:
        reconciliation["collection_rate_basis_points"] = collection_rate_basis_points(
            collected_paise=reconciliation.get("total_collected_paise", 0),
            billed_paise=reconciliation.get("total_billed_paise", 0),
        )
    report["reconciliation"] = reconciliation
    if "activity_counts" not in report:
        report["activity_counts"] = {
            "accepted_visit_count": 0,
            "sale_visit_count": 1 if reconciliation.get("total_billed_paise", 0) > 0 else 0,
            "refund_visit_count": reconciliation.get("refund_visit_count", 0),
            "sale_line_item_count": 1 if reconciliation.get("total_billed_paise", 0) > 0 else 0,
        }
    return report

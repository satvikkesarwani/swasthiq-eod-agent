import logging
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.limits import (
    DEFAULT_MAX_ISSUES_PER_REQUEST,
    DEFAULT_MAX_ISSUES_PER_ROW,
    DEFAULT_MAX_LINE_ITEMS_PER_RECORD,
    DEFAULT_MAX_MEDICINE_COMPARISONS_PER_REPORT,
    DEFAULT_MAX_MEDICINE_WARNINGS_PER_REPORT,
    DEFAULT_MAX_PERSISTED_ISSUES_PER_REPORT,
    DEFAULT_MAX_RECORDS_PER_IMPORT,
    MAX_SAFE_JSON_INTEGER,
)
from app.repositories.clinic_day_repository import ClinicDayRepository
from app.schemas.ingestion import BillingLogRequest
from app.services.report_service import (
    build_deterministic_report,
    build_report_hash_payload,
    build_source_hash_payload,
    canonical_hash,
)
from app.services.row_validator import validate_billing_log

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        session: Session,
        *,
        max_records: int = DEFAULT_MAX_RECORDS_PER_IMPORT,
        max_line_items: int = DEFAULT_MAX_LINE_ITEMS_PER_RECORD,
        max_issues_per_row: int = DEFAULT_MAX_ISSUES_PER_ROW,
        max_issues_per_request: int = DEFAULT_MAX_ISSUES_PER_REQUEST,
        max_persisted_issues: int = DEFAULT_MAX_PERSISTED_ISSUES_PER_REPORT,
        max_medicine_warnings: int = DEFAULT_MAX_MEDICINE_WARNINGS_PER_REPORT,
        max_medicine_comparisons: int = DEFAULT_MAX_MEDICINE_COMPARISONS_PER_REPORT,
        max_safe_paise: int = MAX_SAFE_JSON_INTEGER,
        store_rejected_raw_rows: bool = False,
    ):
        self.session = session
        self.max_records = max_records
        self.max_line_items = max_line_items
        self.max_issues_per_row = max_issues_per_row
        self.max_issues_per_request = max_issues_per_request
        self.max_persisted_issues = max_persisted_issues
        self.max_medicine_warnings = max_medicine_warnings
        self.max_medicine_comparisons = max_medicine_comparisons
        self.max_safe_paise = max_safe_paise
        self.store_rejected_raw_rows = store_rejected_raw_rows
        self.repository = ClinicDayRepository(session)

    def replace_clinic_day(
        self, *, clinic_id: str, business_date: date, request: BillingLogRequest
    ) -> tuple[Any, str]:
        logger.info(
            "ingestion.replace start clinic_id=%s business_date=%s records=%s max_records=%s",
            clinic_id,
            business_date,
            len(request.records),
            self.max_records,
        )
        if len(request.records) > self.max_records:
            logger.warning(
                "ingestion.replace too_many_records clinic_id=%s business_date=%s records=%s max_records=%s",
                clinic_id,
                business_date,
                len(request.records),
                self.max_records,
            )
            raise AppError(
                code="REQUEST_TOO_LARGE",
                message=f"A maximum of {self.max_records} records is allowed per request.",
                status_code=413,
            )

        ingestion = validate_billing_log(
            clinic_id=clinic_id,
            business_date=business_date,
            records=request.records,
            max_line_items=self.max_line_items,
            max_issues_per_row=self.max_issues_per_row,
            max_issues_per_request=self.max_issues_per_request,
            max_safe_paise=self.max_safe_paise,
        )
        persisted_issues = ingestion.rejected[: self.max_persisted_issues]
        persisted_truncated = ingestion.issues_truncated or len(ingestion.rejected) > len(persisted_issues)
        logger.info(
            "ingestion.validation complete clinic_id=%s business_date=%s received=%s accepted=%s total_issues=%s returned_issues=%s persisted_issues=%s rejected_rows=%s truncated=%s",
            clinic_id,
            business_date,
            ingestion.received_rows,
            len(ingestion.accepted),
            ingestion.total_issue_count,
            ingestion.returned_issue_count,
            len(persisted_issues),
            len({issue.row_index for issue in ingestion.rejected}),
            persisted_truncated,
        )
        if request.records and not ingestion.accepted:
            logger.warning(
                "ingestion.replace no_valid_records clinic_id=%s business_date=%s rejected_issues=%s",
                clinic_id,
                business_date,
                len(ingestion.rejected),
            )
            raise AppError(
                code="NO_VALID_RECORDS",
                message="The billing log contains no valid rows; the existing clinic-day was not changed.",
                status_code=422,
                details=[issue.model_dump(exclude={"raw_row"}) for issue in ingestion.rejected],
            )

        report = build_deterministic_report(
            ingestion.accepted,
            max_medicine_warnings=self.max_medicine_warnings,
            max_medicine_comparisons=self.max_medicine_comparisons,
            max_safe_paise=self.max_safe_paise,
        )
        status = "completed_with_errors" if ingestion.rejected else "completed"
        rejected_row_count = len({issue.row_index for issue in ingestion.rejected})
        source_hash = canonical_hash(
            build_source_hash_payload(
                clinic_id=clinic_id,
                business_date=business_date.isoformat(),
                clinic_name=request.clinic_name,
                clinic_location=request.clinic_location,
                records=request.records,
            )
        )
        report_hash = canonical_hash(
            build_report_hash_payload(
                clinic_id=clinic_id,
                business_date=business_date.isoformat(),
                accepted_rows=len(ingestion.accepted),
                rejected_rows=rejected_row_count,
                report=report,
            )
        )

        try:
            with self.session.begin():
                logger.info(
                    "ingestion.repository_replace start clinic_id=%s business_date=%s status=%s source_hash=%s report_hash=%s",
                    clinic_id,
                    business_date,
                    status,
                    source_hash,
                    report_hash,
                )
                clinic_day, operation = self.repository.replace(
                    clinic_id=clinic_id,
                    clinic_name=request.clinic_name,
                    clinic_location=request.clinic_location,
                    business_date=business_date,
                    status=status,
                    received_rows=ingestion.received_rows,
                    rejected_row_count=rejected_row_count,
                    total_issue_count=ingestion.total_issue_count,
                    returned_issue_count=len(persisted_issues),
                    issues_truncated=persisted_truncated,
                    accepted=ingestion.accepted,
                    rejected=persisted_issues,
                    store_rejected_raw_rows=self.store_rejected_raw_rows,
                    source_hash=source_hash,
                    report_hash=report_hash,
                    report_json=report.model_dump(mode="json"),
                )
        except Exception:
            logger.exception("ingestion.repository_replace failed clinic_id=%s business_date=%s", clinic_id, business_date)
            self.session.rollback()
            raise

        logger.info(
            "ingestion.replace done clinic_id=%s business_date=%s operation=%s status=%s",
            clinic_id,
            business_date,
            operation,
            status,
        )
        return self.repository.get(clinic_id, business_date, with_children=True), operation

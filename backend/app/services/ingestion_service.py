from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.repositories.clinic_day_repository import ClinicDayRepository
from app.schemas.ingestion import BillingLogRequest
from app.services.report_service import (
    build_deterministic_report,
    build_report_hash_payload,
    build_source_hash_payload,
    canonical_hash,
)
from app.services.row_validator import validate_billing_log


class IngestionService:
    def __init__(
        self,
        session: Session,
        *,
        max_records: int = 10_000,
        store_rejected_raw_rows: bool = False,
    ):
        self.session = session
        self.max_records = max_records
        self.store_rejected_raw_rows = store_rejected_raw_rows
        self.repository = ClinicDayRepository(session)

    def replace_clinic_day(
        self, *, clinic_id: str, business_date: date, request: BillingLogRequest
    ) -> tuple[Any, str]:
        if len(request.records) > self.max_records:
            raise AppError(
                code="REQUEST_TOO_LARGE",
                message=f"A maximum of {self.max_records} records is allowed per request.",
                status_code=413,
            )

        ingestion = validate_billing_log(
            clinic_id=clinic_id, business_date=business_date, records=request.records
        )
        if request.records and not ingestion.accepted:
            raise AppError(
                code="NO_VALID_RECORDS",
                message="The billing log contains no valid rows; the existing clinic-day was not changed.",
                status_code=422,
                details=[issue.model_dump(exclude={"raw_row"}) for issue in ingestion.rejected],
            )

        report = build_deterministic_report(ingestion.accepted)
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
                clinic_day, operation = self.repository.replace(
                    clinic_id=clinic_id,
                    clinic_name=request.clinic_name,
                    clinic_location=request.clinic_location,
                    business_date=business_date,
                    status=status,
                    received_rows=ingestion.received_rows,
                    rejected_row_count=rejected_row_count,
                    accepted=ingestion.accepted,
                    rejected=ingestion.rejected,
                    store_rejected_raw_rows=self.store_rejected_raw_rows,
                    source_hash=source_hash,
                    report_hash=report_hash,
                    report_json=report.model_dump(mode="json"),
                )
        except Exception:
            self.session.rollback()
            raise

        return self.repository.get(clinic_id, business_date, with_children=True), operation

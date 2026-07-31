import logging
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

logger = logging.getLogger(__name__)


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
            clinic_id=clinic_id, business_date=business_date, records=request.records
        )
        logger.info(
            "ingestion.validation complete clinic_id=%s business_date=%s received=%s accepted=%s rejected_issues=%s rejected_rows=%s",
            clinic_id,
            business_date,
            ingestion.received_rows,
            len(ingestion.accepted),
            len(ingestion.rejected),
            len({issue.row_index for issue in ingestion.rejected}),
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
                    accepted=ingestion.accepted,
                    rejected=ingestion.rejected,
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

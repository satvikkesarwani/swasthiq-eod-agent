from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ClinicDay, IngestionError, LineItem, Visit
from app.schemas.ingestion import RowIssue, ValidatedVisit


class ClinicDayRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, clinic_id: str, business_date: date, *, with_children: bool = True) -> ClinicDay | None:
        statement = select(ClinicDay).where(
            ClinicDay.clinic_id == clinic_id,
            ClinicDay.business_date == business_date,
        )
        if with_children:
            statement = statement.options(
                selectinload(ClinicDay.ingestion_errors),
                selectinload(ClinicDay.narrative),
            )
        return self.session.scalar(statement)

    def list_all(self, clinic_id: str | None = None) -> list[ClinicDay]:
        statement = select(ClinicDay).options(selectinload(ClinicDay.narrative)).order_by(
            ClinicDay.business_date.desc(), ClinicDay.updated_at.desc()
        )
        if clinic_id:
            statement = statement.where(ClinicDay.clinic_id == clinic_id)
        return list(self.session.scalars(statement).all())

    def replace(
        self,
        *,
        clinic_id: str,
        clinic_name: str,
        clinic_location: str,
        business_date: date,
        status: str,
        received_rows: int,
        rejected_row_count: int,
        accepted: list[ValidatedVisit],
        rejected: list[RowIssue],
        store_rejected_raw_rows: bool,
        source_hash: str,
        report_hash: str,
        report_json: dict[str, Any],
    ) -> tuple[ClinicDay, bool]:
        clinic_day = self.get(clinic_id, business_date, with_children=True)
        created = clinic_day is None
        if clinic_day is None:
            clinic_day = ClinicDay(
                clinic_id=clinic_id,
                clinic_name=clinic_name,
                clinic_location=clinic_location,
                business_date=business_date,
                status=status,
                received_rows=received_rows,
                accepted_rows=len(accepted),
                rejected_rows=rejected_row_count,
                source_hash=source_hash,
                report_hash=report_hash,
                report_json=report_json,
            )
            self.session.add(clinic_day)
            self.session.flush()
        else:
            previous_hash = clinic_day.report_hash
            clinic_day.clinic_name = clinic_name
            clinic_day.clinic_location = clinic_location
            clinic_day.status = status
            clinic_day.received_rows = received_rows
            clinic_day.accepted_rows = len(accepted)
            clinic_day.rejected_rows = rejected_row_count
            clinic_day.source_hash = source_hash
            clinic_day.report_hash = report_hash
            clinic_day.report_json = report_json
            clinic_day.visits.clear()
            clinic_day.ingestion_errors.clear()
            if previous_hash != report_hash and clinic_day.narrative is not None:
                self.session.delete(clinic_day.narrative)
                clinic_day.narrative = None
            self.session.flush()

        for accepted_visit in accepted:
            visit_model = Visit(
                visit_id=accepted_visit.visit_id,
                timestamp_utc=accepted_visit.timestamp,
                doctor_id=accepted_visit.doctor_id,
                payment_mode=accepted_visit.payment_mode.value,
                amount_paid_paise=accepted_visit.amount_paid_paise,
                discount_paise=accepted_visit.discount_paise,
                is_refund=accepted_visit.is_refund,
                gross_line_total_paise=accepted_visit.gross_line_total_paise,
                billed_paise=accepted_visit.billed_paise,
                outstanding_paise=accepted_visit.outstanding_paise,
            )
            visit_model.line_items = [
                LineItem(
                    drug_name_source=item.drug_name_source,
                    drug_name_normalized=item.drug_name_normalized,
                    qty=item.qty,
                    unit_price_paise=item.unit_price_paise,
                    gross_revenue_paise=item.gross_revenue_paise,
                )
                for item in accepted_visit.line_items
            ]
            clinic_day.visits.append(visit_model)

        for issue in rejected:
            clinic_day.ingestion_errors.append(
                IngestionError(
                    row_index=issue.row_index,
                    visit_id=issue.visit_id,
                    field_path=issue.field,
                    code=issue.code,
                    message=issue.message,
                    raw_row_json=issue.raw_row if store_rejected_raw_rows else None,
                )
            )

        self.session.flush()
        return clinic_day, created

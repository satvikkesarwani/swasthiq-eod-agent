import logging
from datetime import date
from typing import Any

from pydantic import ValidationError

from app.schemas.ingestion import (
    BillingVisitInput,
    IngestionResult,
    NormalizedLineItem,
    RowIssue,
    ValidatedVisit,
)

logger = logging.getLogger(__name__)


def normalize_drug_name(value: str) -> str:
    return " ".join(value.split()).upper()


def _field_path(location: tuple[Any, ...]) -> str:
    return ".".join(str(part) for part in location)


def _error_code(error_type: str) -> str:
    if error_type == "missing":
        return "FIELD_REQUIRED"
    if error_type.startswith("extra_forbidden"):
        return "UNKNOWN_FIELD"
    if "enum" in error_type:
        return "INVALID_ENUM"
    if "datetime" in error_type or error_type == "value_error":
        return "INVALID_VALUE"
    return "SCHEMA_VALIDATION_FAILED"


def validate_billing_log(
    *, clinic_id: str, business_date: date, records: list[dict[str, Any]]
) -> IngestionResult:
    logger.info(
        "row_validator.start clinic_id=%s business_date=%s records=%s",
        clinic_id,
        business_date,
        len(records),
    )
    accepted: list[ValidatedVisit] = []
    rejected: list[RowIssue] = []
    seen_visit_ids: set[str] = set()

    for row_index, raw_row in enumerate(records):
        visit_id = raw_row.get("visit_id") if isinstance(raw_row, dict) else None
        if not isinstance(raw_row, dict):
            logger.warning(
                "row_validator.reject row=%s code=ROW_MUST_BE_OBJECT raw_type=%s",
                row_index,
                type(raw_row).__name__,
            )
            rejected.append(
                RowIssue(
                    row_index=row_index,
                    field="$",
                    code="ROW_MUST_BE_OBJECT",
                    message="Each billing row must be a JSON object.",
                    raw_row=None,
                )
            )
            continue

        try:
            parsed = BillingVisitInput.model_validate(raw_row)
        except ValidationError as exc:
            for error in exc.errors(include_url=False):
                logger.warning(
                    "row_validator.reject row=%s visit_id=%s field=%s code=%s message=%s",
                    row_index,
                    visit_id,
                    _field_path(error["loc"]),
                    _error_code(error["type"]),
                    error["msg"],
                )
                rejected.append(
                    RowIssue(
                        row_index=row_index,
                        visit_id=str(visit_id) if visit_id is not None else None,
                        field=_field_path(error["loc"]),
                        code=_error_code(error["type"]),
                        message=error["msg"],
                        raw_row=raw_row,
                    )
                )
            continue

        domain_issues: list[RowIssue] = []
        if parsed.clinic_id != clinic_id:
            domain_issues.append(
                RowIssue(
                    row_index=row_index,
                    visit_id=parsed.visit_id,
                    field="clinic_id",
                    code="CLINIC_ID_MISMATCH",
                    message=f"Row clinic_id must match route clinic_id '{clinic_id}'.",
                    raw_row=raw_row,
                )
            )
        if parsed.timestamp.date() != business_date:
            domain_issues.append(
                RowIssue(
                    row_index=row_index,
                    visit_id=parsed.visit_id,
                    field="timestamp",
                    code="BUSINESS_DATE_MISMATCH",
                    message=f"UTC timestamp date must be {business_date.isoformat()}.",
                    raw_row=raw_row,
                )
            )
        if parsed.visit_id in seen_visit_ids:
            domain_issues.append(
                RowIssue(
                    row_index=row_index,
                    visit_id=parsed.visit_id,
                    field="visit_id",
                    code="DUPLICATE_VISIT_ID",
                    message="visit_id must be unique within a clinic-day upload.",
                    raw_row=raw_row,
                )
            )

        gross_total = sum(item.qty * item.unit_price_paise for item in parsed.line_items)
        billed = 0 if parsed.is_refund else gross_total - parsed.discount_paise
        outstanding = 0 if parsed.is_refund else billed - parsed.amount_paid_paise

        if parsed.discount_paise > gross_total:
            domain_issues.append(
                RowIssue(
                    row_index=row_index,
                    visit_id=parsed.visit_id,
                    field="discount_paise",
                    code="DISCOUNT_EXCEEDS_GROSS",
                    message="discount_paise cannot exceed the line-item gross total.",
                    raw_row=raw_row,
                )
            )
        if parsed.is_refund:
            if parsed.amount_paid_paise >= 0:
                domain_issues.append(
                    RowIssue(
                        row_index=row_index,
                        visit_id=parsed.visit_id,
                        field="amount_paid_paise",
                        code="INVALID_REFUND_SIGN",
                        message="A refund row must have a negative amount_paid_paise.",
                        raw_row=raw_row,
                    )
                )
        else:
            if parsed.amount_paid_paise < 0:
                domain_issues.append(
                    RowIssue(
                        row_index=row_index,
                        visit_id=parsed.visit_id,
                        field="amount_paid_paise",
                        code="NEGATIVE_NON_REFUND_PAYMENT",
                        message="A non-refund row cannot have a negative amount_paid_paise.",
                        raw_row=raw_row,
                    )
                )
            if billed >= 0 and parsed.amount_paid_paise > billed:
                domain_issues.append(
                    RowIssue(
                        row_index=row_index,
                        visit_id=parsed.visit_id,
                        field="amount_paid_paise",
                        code="PAYMENT_EXCEEDS_BILLED",
                        message="amount_paid_paise cannot exceed the net billed amount.",
                        raw_row=raw_row,
                    )
                )

        if domain_issues:
            for issue in domain_issues:
                logger.warning(
                    "row_validator.reject row=%s visit_id=%s field=%s code=%s message=%s",
                    issue.row_index,
                    issue.visit_id,
                    issue.field,
                    issue.code,
                    issue.message,
                )
            rejected.extend(domain_issues)
            continue

        seen_visit_ids.add(parsed.visit_id)
        normalized_items = [
            NormalizedLineItem(
                drug_name_source=item.drug_name,
                drug_name_normalized=normalize_drug_name(item.drug_name),
                qty=item.qty,
                unit_price_paise=item.unit_price_paise,
                gross_revenue_paise=item.qty * item.unit_price_paise,
            )
            for item in parsed.line_items
        ]
        accepted.append(
            ValidatedVisit(
                clinic_id=parsed.clinic_id,
                visit_id=parsed.visit_id,
                timestamp=parsed.timestamp,
                doctor_id=parsed.doctor_id,
                line_items=normalized_items,
                payment_mode=parsed.payment_mode,
                amount_paid_paise=parsed.amount_paid_paise,
                discount_paise=parsed.discount_paise,
                is_refund=parsed.is_refund,
                gross_line_total_paise=gross_total,
                billed_paise=billed,
                outstanding_paise=outstanding,
            )
        )
        logger.debug(
            "row_validator.accept row=%s visit_id=%s payment_mode=%s billed_paise=%s paid_paise=%s line_items=%s",
            row_index,
            parsed.visit_id,
            parsed.payment_mode.value,
            billed,
            parsed.amount_paid_paise,
            len(parsed.line_items),
        )

    logger.info(
        "row_validator.done clinic_id=%s business_date=%s received=%s accepted=%s rejected_issues=%s rejected_rows=%s",
        clinic_id,
        business_date,
        len(records),
        len(accepted),
        len(rejected),
        len({issue.row_index for issue in rejected}),
    )
    return IngestionResult(
        clinic_id=clinic_id,
        business_date=business_date,
        received_rows=len(records),
        accepted=accepted,
        rejected=rejected,
    )

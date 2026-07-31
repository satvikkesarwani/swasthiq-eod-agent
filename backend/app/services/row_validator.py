import logging
from datetime import date
from typing import Any

from pydantic import ValidationError

from app.core.limits import DEFAULT_MAX_ISSUES_PER_REQUEST, DEFAULT_MAX_ISSUES_PER_ROW, DEFAULT_MAX_LINE_ITEMS_PER_RECORD, MAX_SAFE_JSON_INTEGER
from app.core.limits import MAX_VISIT_ID_LENGTH
from app.core.money import checked_mul_paise, checked_sub_paise, checked_sum_paise, require_safe_paise
from app.core.safe_strings import is_safe_display_identifier, safe_error_code, safe_error_message, safe_field_path
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
    return safe_field_path(".".join(str(part) for part in location))


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


def _mapped_error_code(error_type: str, field: str) -> str:
    if field == "payment_mode" and error_type == "value_error":
        return "INVALID_ENUM"
    return _error_code(error_type)


def _safe_visit_id(raw_row: Any) -> str | None:
    if not isinstance(raw_row, dict):
        return None
    value = raw_row.get("visit_id")
    if isinstance(value, str) and is_safe_display_identifier(value, max_length=MAX_VISIT_ID_LENGTH):
        return value
    return None


def _append_issue(
    rejected: list[RowIssue],
    *,
    issue: RowIssue,
    total_issue_count: int,
    max_issues_per_request: int,
) -> tuple[int, bool]:
    total_issue_count += 1
    if len(rejected) >= max_issues_per_request:
        return total_issue_count, True
    rejected.append(issue)
    return total_issue_count, False


def validate_billing_log(
    *,
    clinic_id: str,
    business_date: date,
    records: list[dict[str, Any]],
    max_line_items: int = DEFAULT_MAX_LINE_ITEMS_PER_RECORD,
    max_issues_per_row: int = DEFAULT_MAX_ISSUES_PER_ROW,
    max_issues_per_request: int = DEFAULT_MAX_ISSUES_PER_REQUEST,
    max_safe_paise: int = MAX_SAFE_JSON_INTEGER,
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
    total_issue_count = 0
    issues_truncated = False

    for row_index, raw_row in enumerate(records):
        if len(rejected) >= max_issues_per_request:
            issues_truncated = True
            break
        safe_visit_id = _safe_visit_id(raw_row)
        if not isinstance(raw_row, dict):
            logger.warning(
                "row_validator.reject row=%s code=ROW_MUST_BE_OBJECT raw_type=%s",
                row_index,
                type(raw_row).__name__,
            )
            total_issue_count, truncated_now = _append_issue(
                rejected,
                total_issue_count=total_issue_count,
                max_issues_per_request=max_issues_per_request,
                issue=RowIssue(
                    row_index=row_index,
                    field="$",
                    code="ROW_MUST_BE_OBJECT",
                    message="Each billing row must be a JSON object.",
                    raw_row=None,
                ),
            )
            issues_truncated = issues_truncated or truncated_now
            continue

        if isinstance(raw_row.get("line_items"), list) and len(raw_row["line_items"]) > max_line_items:
            logger.warning("row_validator.reject row=%s code=TOO_MANY_LINE_ITEMS line_items=%s", row_index, len(raw_row["line_items"]))
            total_issue_count, truncated_now = _append_issue(
                rejected,
                total_issue_count=total_issue_count,
                max_issues_per_request=max_issues_per_request,
                issue=RowIssue(
                    row_index=row_index,
                    visit_id=safe_visit_id,
                    field="line_items",
                    code="TOO_MANY_LINE_ITEMS",
                    message=f"A billing row may contain at most {max_line_items} line items.",
                    raw_row=raw_row,
                ),
            )
            issues_truncated = issues_truncated or truncated_now
            continue

        try:
            parsed = BillingVisitInput.model_validate(raw_row)
        except ValidationError as exc:
            for error in exc.errors(include_url=False)[:max_issues_per_row]:
                field = _field_path(error["loc"])
                code = safe_error_code(_mapped_error_code(error["type"], field))
                message = safe_error_message(error["msg"])
                logger.warning(
                    "row_validator.reject row=%s visit_id_present=%s field=%s code=%s",
                    row_index,
                    safe_visit_id is not None,
                    field,
                    code,
                )
                total_issue_count, truncated_now = _append_issue(
                    rejected,
                    total_issue_count=total_issue_count,
                    max_issues_per_request=max_issues_per_request,
                    issue=RowIssue(
                        row_index=row_index,
                        visit_id=safe_visit_id,
                        field=field,
                        code=code,
                        message=message,
                        raw_row=raw_row,
                    ),
                )
                issues_truncated = issues_truncated or truncated_now
            if len(exc.errors(include_url=False)) > max_issues_per_row:
                total_issue_count += len(exc.errors(include_url=False)) - max_issues_per_row
                issues_truncated = True
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

        gross_total = checked_sum_paise(
            [
                checked_mul_paise(item.qty, item.unit_price_paise, field="line_items.gross_revenue_paise", max_abs=max_safe_paise)
                for item in parsed.line_items
            ],
            field="gross_line_total_paise",
            max_abs=max_safe_paise,
        )
        require_safe_paise(parsed.amount_paid_paise, field="amount_paid_paise", max_abs=max_safe_paise)
        require_safe_paise(parsed.discount_paise, field="discount_paise", max_abs=max_safe_paise)
        billed = 0 if parsed.is_refund else checked_sub_paise(gross_total, parsed.discount_paise, field="billed_paise", max_abs=max_safe_paise)
        outstanding = 0 if parsed.is_refund else checked_sub_paise(billed, parsed.amount_paid_paise, field="outstanding_paise", max_abs=max_safe_paise)

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
                    "row_validator.reject row=%s visit_id_present=%s field=%s code=%s",
                    issue.row_index,
                    issue.visit_id is not None,
                    issue.field,
                    issue.code,
                )
                total_issue_count, truncated_now = _append_issue(
                    rejected,
                    total_issue_count=total_issue_count,
                    max_issues_per_request=max_issues_per_request,
                    issue=issue,
                )
                issues_truncated = issues_truncated or truncated_now
            continue

        seen_visit_ids.add(parsed.visit_id)
        normalized_items = [
            NormalizedLineItem(
                drug_name_source=item.drug_name,
                drug_name_normalized=normalize_drug_name(item.drug_name),
                qty=item.qty,
                unit_price_paise=item.unit_price_paise,
                gross_revenue_paise=checked_mul_paise(item.qty, item.unit_price_paise, field="line_items.gross_revenue_paise", max_abs=max_safe_paise),
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
            "row_validator.accept row=%s visit_id_present=%s payment_mode=%s line_items=%s is_refund=%s",
            row_index,
            True,
            parsed.payment_mode.value,
            len(parsed.line_items),
            parsed.is_refund,
        )

    logger.info(
        "row_validator.done clinic_id=%s business_date=%s received=%s accepted=%s rejected_issues=%s rejected_rows=%s",
        clinic_id,
        business_date,
        len(records),
        len(accepted),
        total_issue_count,
        len({issue.row_index for issue in rejected}),
    )
    return IngestionResult(
        clinic_id=clinic_id,
        business_date=business_date,
        received_rows=len(records),
        accepted=accepted,
        rejected=rejected,
        total_issue_count=total_issue_count,
        returned_issue_count=len(rejected),
        issues_truncated=issues_truncated,
    )

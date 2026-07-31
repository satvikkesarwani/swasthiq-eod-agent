from datetime import date

import pytest

from app.services.report_service import build_deterministic_report
from app.services.row_validator import validate_billing_log


BUSINESS_DATE = date(2026, 7, 27)


def row(
    *,
    visit_id: str = "V-1",
    timestamp: str = "2026-07-27T09:00:00Z",
    drug_name: str = "MED-A",
    qty: int = 1,
    unit_price_paise: int = 1_000,
    payment_mode: str = "cash",
    amount_paid_paise: int = 1_000,
    discount_paise: int = 0,
    is_refund: bool = False,
    clinic_id: str = "CLN-001",
) -> dict:
    return {
        "clinic_id": clinic_id,
        "visit_id": visit_id,
        "timestamp": timestamp,
        "doctor_id": "DOC-1",
        "line_items": [{"drug_name": drug_name, "qty": qty, "unit_price_paise": unit_price_paise}],
        "payment_mode": payment_mode,
        "amount_paid_paise": amount_paid_paise,
        "discount_paise": discount_paise,
        "is_refund": is_refund,
    }


def assert_reconciliation_invariants(report):
    reconciliation = report.reconciliation
    payment_rows = reconciliation.by_payment_mode.values()
    assert reconciliation.total_billed_paise == sum(row.billed_paise for row in payment_rows)
    assert reconciliation.total_collected_paise == sum(row.collected_paise for row in payment_rows)
    assert reconciliation.total_outstanding_paise == sum(row.outstanding_paise for row in payment_rows)
    assert reconciliation.total_refunds_paise == sum(row.refunds_paise for row in payment_rows)
    assert reconciliation.total_outstanding_paise == (
        reconciliation.total_billed_paise - reconciliation.total_collected_paise
    )


def test_non_object_row_is_rejected():
    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=["not an object"])
    assert result.received_rows == 1
    assert not result.accepted
    assert result.rejected[0].code == "ROW_MUST_BE_OBJECT"
    assert result.rejected[0].raw_row is None
    assert result.total_issue_count == 1
    assert result.returned_issue_count == 1


@pytest.mark.parametrize(
    ("mutate", "field", "code"),
    [
        (lambda item: item.pop("payment_mode"), "payment_mode", "FIELD_REQUIRED"),
        (lambda item: item.update(payment_mode="wallet"), "payment_mode", "INVALID_ENUM"),
        (lambda item: item.update(clinic_id="CLN-OTHER"), "clinic_id", "CLINIC_ID_MISMATCH"),
        (lambda item: item.update(timestamp="2026-07-28T00:00:00Z"), "timestamp", "BUSINESS_DATE_MISMATCH"),
        (lambda item: item.update(discount_paise=1_001), "discount_paise", "DISCOUNT_EXCEEDS_GROSS"),
        (lambda item: item.update(is_refund=True, amount_paid_paise=0), "amount_paid_paise", "INVALID_REFUND_SIGN"),
        (lambda item: item.update(amount_paid_paise=-1), "amount_paid_paise", "NEGATIVE_NON_REFUND_PAYMENT"),
        (lambda item: item.update(amount_paid_paise=1_001), "amount_paid_paise", "PAYMENT_EXCEEDS_BILLED"),
        (lambda item: item.update(timestamp="2026-07-27T09:00:00+05:30"), "timestamp", "INVALID_VALUE"),
        (
            lambda item: item.update(line_items=[{"drug_name": "MED-A", "qty": 1, "unit_price_paise": -1}]),
            "line_items.0.unit_price_paise",
            "SCHEMA_VALIDATION_FAILED",
        ),
    ],
)
def test_row_validation_rejects_locked_error_branches(mutate, field, code):
    candidate = row()
    mutate(candidate)

    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=[candidate])

    assert not result.accepted
    assert any(issue.field == field and issue.code == code for issue in result.rejected)


def test_duplicate_visit_id_rejects_second_row_only():
    rows = [row(visit_id="DUP"), row(visit_id="DUP", timestamp="2026-07-27T10:00:00Z")]
    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=rows)

    assert len(result.accepted) == 1
    assert len(result.rejected) == 1
    assert result.rejected[0].code == "DUPLICATE_VISIT_ID"
    assert result.rejected[0].row_index == 1


def test_multiple_validation_errors_on_one_row_have_one_rejected_row_index():
    candidate = row()
    candidate.pop("payment_mode")
    candidate["doctor_id"] = ""
    candidate["line_items"] = [{"drug_name": "", "qty": 0, "unit_price_paise": -1}]
    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=[candidate])

    assert len(result.rejected) > 1
    assert len({issue.row_index for issue in result.rejected}) == 1


def test_partial_ingestion_excludes_rejected_rows_from_outputs():
    valid = row(visit_id="GOOD", amount_paid_paise=1_000)
    invalid = row(visit_id="BAD", amount_paid_paise=99_999)
    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=[valid, invalid])
    report = build_deterministic_report(result.accepted)

    assert len(result.accepted) == 1
    assert report.reconciliation.total_billed_paise == 1_000
    assert report.analytics.revenue_by_hour[9].revenue_paise == 1_000
    assert_reconciliation_invariants(report)
    assert report.activity_counts.sale_visit_count == 1
    assert report.activity_counts.refund_visit_count == 0
    assert report.reconciliation.collection_rate_basis_points == 10000


def test_refunds_do_not_contribute_to_sales_or_medicine_rankings():
    refund = row(
        visit_id="REFUND",
        is_refund=True,
        amount_paid_paise=-9_000,
        qty=9,
        unit_price_paise=1_000,
        payment_mode="upi",
    )
    sale = row(visit_id="SALE", timestamp="2026-07-27T12:00:00Z", drug_name="MED-B")
    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=[refund, sale])
    report = build_deterministic_report(result.accepted)

    assert report.reconciliation.total_refunds_paise == 9_000
    assert report.reconciliation.total_billed_paise == 1_000
    assert report.analytics.revenue_by_hour[9].revenue_paise == 0
    assert report.analytics.top_medicines_by_quantity[0].drug_name == "MED-B"
    assert report.activity_counts.sale_visit_count == 1
    assert report.activity_counts.refund_visit_count == 1
    assert_reconciliation_invariants(report)


def test_peak_hour_tie_breaks_to_earliest_utc_hour():
    rows = [
        row(visit_id="LATE", timestamp="2026-07-27T16:00:00Z"),
        row(visit_id="EARLY", timestamp="2026-07-27T08:00:00Z"),
    ]
    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=rows)
    report = build_deterministic_report(result.accepted)

    assert report.analytics.peak_hour.start_hour_utc == 8


def test_medicine_quantity_and_revenue_rankings_are_separate():
    rows = [
        row(visit_id="QTY", drug_name="LOW PRICE", qty=10, unit_price_paise=100, amount_paid_paise=1_000),
        row(visit_id="REV", drug_name="HIGH PRICE", qty=1, unit_price_paise=2_000, amount_paid_paise=2_000),
    ]
    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=rows)
    report = build_deterministic_report(result.accepted)

    assert report.analytics.top_medicines_by_quantity[0].drug_name == "LOW PRICE"
    assert report.analytics.top_medicines_by_revenue[0].drug_name == "HIGH PRICE"
    assert_reconciliation_invariants(report)


def test_non_refund_visit_financial_invariants_hold_for_discount_and_partial_payment():
    candidate = row(qty=3, unit_price_paise=1_000, amount_paid_paise=2_000, discount_paise=500)
    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=[candidate])
    visit = result.accepted[0]
    report = build_deterministic_report(result.accepted)

    assert visit.billed_paise == visit.gross_line_total_paise - visit.discount_paise
    assert visit.outstanding_paise == visit.billed_paise - visit.amount_paid_paise
    assert report.reconciliation.pending_visit_count == 1
    assert_reconciliation_invariants(report)


def test_issue_count_is_capped_but_total_is_preserved():
    candidate = row()
    candidate.pop("payment_mode")
    candidate["doctor_id"] = ""
    candidate["line_items"] = [{"drug_name": "", "qty": 0, "unit_price_paise": -1}]

    result = validate_billing_log(
        clinic_id="CLN-001",
        business_date=BUSINESS_DATE,
        records=[candidate],
        max_issues_per_row=2,
        max_issues_per_request=2,
    )

    assert result.total_issue_count > result.returned_issue_count
    assert result.returned_issue_count == 2
    assert result.issues_truncated is True


def test_rejects_stringified_integer_without_coercion():
    candidate = row()
    candidate["amount_paid_paise"] = "1000"

    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=[candidate])

    assert not result.accepted
    assert result.rejected[0].field == "amount_paid_paise"
    assert result.rejected[0].code == "SCHEMA_VALIDATION_FAILED"


def test_refund_only_activity_count_prevents_empty_classification():
    refund = row(visit_id="REF", is_refund=True, amount_paid_paise=-1_000)
    result = validate_billing_log(clinic_id="CLN-001", business_date=BUSINESS_DATE, records=[refund])
    report = build_deterministic_report(result.accepted)

    assert report.reconciliation.total_billed_paise == 0
    assert report.activity_counts.accepted_visit_count == 1
    assert report.activity_counts.sale_visit_count == 0
    assert report.activity_counts.refund_visit_count == 1

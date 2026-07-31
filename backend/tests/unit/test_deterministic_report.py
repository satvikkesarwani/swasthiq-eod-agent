from datetime import date

from app.services.report_service import build_deterministic_report
from app.services.row_validator import validate_billing_log


def test_reconciliation_and_analytics_are_deterministic(valid_rows):
    result = validate_billing_log(clinic_id="CLN-001", business_date=date(2026, 7, 27), records=valid_rows)
    report = build_deterministic_report(result.accepted)

    assert not result.rejected
    assert report.reconciliation.total_billed_paise == 10_500
    assert report.reconciliation.total_collected_paise == 10_000
    assert report.reconciliation.total_outstanding_paise == 500
    assert report.reconciliation.total_discount_paise == 500
    assert report.reconciliation.by_payment_mode["cash"].outstanding_paise == 500
    assert report.analytics.peak_hour.start_hour_utc == 10
    assert report.analytics.top_medicines_by_quantity[0].drug_name == "PARACETAMOL"
    assert report.analytics.top_medicines_by_quantity[0].quantity == 2
    assert report.analytics.top_medicines_by_revenue[0].drug_name == "AMOXICILLIN"


def test_empty_day_returns_zero_report():
    result = validate_billing_log(clinic_id="CLN-001", business_date=date(2026, 7, 26), records=[])
    report = build_deterministic_report(result.accepted)

    assert report.reconciliation.total_billed_paise == 0
    assert report.reconciliation.collection_rate is None
    assert report.analytics.peak_hour is None
    assert len(report.analytics.revenue_by_hour) == 24
    assert report.analytics.top_medicines_by_quantity == []


def test_refund_only_day_excludes_sales_analytics():
    rows = [{
        "clinic_id": "CLN-001", "visit_id": "R-1", "timestamp": "2026-07-25T10:00:00Z",
        "doctor_id": "DOC-1", "line_items": [{"drug_name": "MED-A", "qty": 1, "unit_price_paise": 5000}],
        "payment_mode": "card", "amount_paid_paise": -5000, "discount_paise": 0, "is_refund": True,
    }]
    result = validate_billing_log(clinic_id="CLN-001", business_date=date(2026, 7, 25), records=rows)
    report = build_deterministic_report(result.accepted)

    assert report.reconciliation.total_refunds_paise == 5000
    assert report.reconciliation.total_billed_paise == 0
    assert report.analytics.peak_hour is None
    assert report.analytics.top_medicines_by_revenue == []


def test_malformed_row_is_rejected_with_actionable_field(valid_rows):
    malformed = dict(valid_rows[0])
    malformed.pop("payment_mode")
    result = validate_billing_log(clinic_id="CLN-001", business_date=date(2026, 7, 27), records=[malformed])

    assert not result.accepted
    assert result.rejected[0].field == "payment_mode"
    assert result.rejected[0].code == "FIELD_REQUIRED"


def test_possible_typo_is_warned_but_not_merged():
    rows = [
        {
            "clinic_id": "CLN-001", "visit_id": "V-1", "timestamp": "2026-07-27T10:00:00Z",
            "doctor_id": "D", "line_items": [{"drug_name": "PARACETAMOL", "qty": 1, "unit_price_paise": 100}],
            "payment_mode": "cash", "amount_paid_paise": 100, "discount_paise": 0, "is_refund": False,
        },
        {
            "clinic_id": "CLN-001", "visit_id": "V-2", "timestamp": "2026-07-27T11:00:00Z",
            "doctor_id": "D", "line_items": [{"drug_name": "PARACETMOL", "qty": 1, "unit_price_paise": 100}],
            "payment_mode": "cash", "amount_paid_paise": 100, "discount_paise": 0, "is_refund": False,
        },
    ]
    result = validate_billing_log(clinic_id="CLN-001", business_date=date(2026, 7, 27), records=rows)
    report = build_deterministic_report(result.accepted)

    assert len(report.analytics.top_medicines_by_quantity) == 2
    assert report.data_quality_warnings[0].code == "POSSIBLE_MEDICINE_NAME_TYPO"

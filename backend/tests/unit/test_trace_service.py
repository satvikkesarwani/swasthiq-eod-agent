from types import SimpleNamespace

import pytest

from app.schemas.narrative import NarrativeCandidate, NarrativeSectionCandidate
from app.services.trace_service import build_trace_catalogue, validate_and_render_candidate


def clinic_day_stub():
    return SimpleNamespace(
        business_date=__import__("datetime").date(2026, 7, 27),
        accepted_rows=2,
        rejected_rows=0,
        report_json={
            "reconciliation": {
                "total_billed_paise": 10000, "total_collected_paise": 9000,
                "total_outstanding_paise": 1000, "total_refunds_paise": 0,
                "total_discount_paise": 0, "collection_rate": 0.9,
                "pending_visit_count": 1, "refund_visit_count": 0,
                "by_payment_mode": {},
            },
            "analytics": {
                "peak_hour": {"start_hour_utc": 10, "end_hour_utc": 11, "revenue_paise": 10000},
                "top_medicines_by_quantity": [{"rank": 1, "drug_name": "MED-A", "quantity": 2}],
                "top_medicines_by_revenue": [{"rank": 1, "drug_name": "MED-A", "revenue_paise": 10000}],
                "revenue_by_hour": [],
            },
            "data_quality_warnings": [],
        },
    )


def test_placeholders_render_from_report_only():
    catalogue = build_trace_catalogue(clinic_day=clinic_day_stub())
    candidate = NarrativeCandidate(sections=[NarrativeSectionCandidate(
        text_template="Collected {{reconciliation.total_collected_paise}}.",
        trace_keys=["reconciliation.total_collected_paise"],
    )], unavailable_metrics=[])
    summary, traces = validate_and_render_candidate(candidate, catalogue)
    assert summary == "Collected ₹90."
    assert traces[0].raw_value == 9000


def test_literal_invented_number_is_rejected():
    catalogue = build_trace_catalogue(clinic_day=clinic_day_stub())
    candidate = NarrativeCandidate(sections=[NarrativeSectionCandidate(
        text_template="Collected ₹999 and {{reconciliation.total_collected_paise}}.",
        trace_keys=["reconciliation.total_collected_paise"],
    )], unavailable_metrics=[])
    with pytest.raises(ValueError, match="Literal digits"):
        validate_and_render_candidate(candidate, catalogue)

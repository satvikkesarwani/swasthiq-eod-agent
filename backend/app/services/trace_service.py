import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.core.money import format_hour_range, format_paise, format_rate
from app.schemas.narrative import FigureTrace, NarrativeCandidate

_PLACEHOLDER_RE = re.compile(r"\{\{([a-zA-Z0-9_.-]+)\}\}")
_DIGIT_RE = re.compile(r"\d")


@dataclass(frozen=True, slots=True)
class TraceValue:
    raw_value: Any
    display_value: str


def build_trace_catalogue(*, clinic_day: Any) -> dict[str, TraceValue]:
    report = clinic_day.report_json
    reconciliation = report["reconciliation"]
    analytics = report["analytics"]
    catalogue: dict[str, TraceValue] = {
        "metadata.business_date": TraceValue(clinic_day.business_date.isoformat(), clinic_day.business_date.strftime("%d %b %Y")),
        "ingestion.accepted_rows": TraceValue(clinic_day.accepted_rows, str(clinic_day.accepted_rows)),
        "ingestion.rejected_rows": TraceValue(clinic_day.rejected_rows, str(clinic_day.rejected_rows)),
        "reconciliation.total_billed_paise": TraceValue(reconciliation["total_billed_paise"], format_paise(reconciliation["total_billed_paise"])),
        "reconciliation.total_collected_paise": TraceValue(reconciliation["total_collected_paise"], format_paise(reconciliation["total_collected_paise"])),
        "reconciliation.total_outstanding_paise": TraceValue(reconciliation["total_outstanding_paise"], format_paise(reconciliation["total_outstanding_paise"])),
        "reconciliation.total_refunds_paise": TraceValue(reconciliation["total_refunds_paise"], format_paise(reconciliation["total_refunds_paise"])),
        "reconciliation.total_discount_paise": TraceValue(reconciliation["total_discount_paise"], format_paise(reconciliation["total_discount_paise"])),
        "reconciliation.collection_rate": TraceValue(reconciliation["collection_rate"], format_rate(reconciliation["collection_rate"])),
        "reconciliation.pending_visit_count": TraceValue(reconciliation["pending_visit_count"], str(reconciliation["pending_visit_count"])),
        "reconciliation.refund_visit_count": TraceValue(reconciliation["refund_visit_count"], str(reconciliation["refund_visit_count"])),
    }

    peak = analytics.get("peak_hour")
    if peak:
        catalogue["analytics.peak_hour.label"] = TraceValue(
            {"start_hour_utc": peak["start_hour_utc"], "end_hour_utc": peak["end_hour_utc"]},
            format_hour_range(peak["start_hour_utc"], peak["end_hour_utc"]),
        )
        catalogue["analytics.peak_hour.revenue_paise"] = TraceValue(
            peak["revenue_paise"], format_paise(peak["revenue_paise"])
        )

    for index, item in enumerate(analytics["top_medicines_by_quantity"]):
        catalogue[f"analytics.top_medicines_by_quantity.{index}.drug_name"] = TraceValue(item["drug_name"], item["drug_name"])
        catalogue[f"analytics.top_medicines_by_quantity.{index}.quantity"] = TraceValue(item["quantity"], str(item["quantity"]))
    for index, item in enumerate(analytics["top_medicines_by_revenue"]):
        catalogue[f"analytics.top_medicines_by_revenue.{index}.drug_name"] = TraceValue(item["drug_name"], item["drug_name"])
        catalogue[f"analytics.top_medicines_by_revenue.{index}.revenue_paise"] = TraceValue(item["revenue_paise"], format_paise(item["revenue_paise"]))
    return catalogue


def validate_and_render_candidate(
    candidate: NarrativeCandidate, catalogue: dict[str, TraceValue]
) -> tuple[str, list[FigureTrace]]:
    rendered_sections: list[str] = []
    trace_order: list[str] = []

    for section in candidate.sections:
        placeholders = _PLACEHOLDER_RE.findall(section.text_template)
        if set(placeholders) != set(section.trace_keys):
            raise ValueError("Each trace_key must match exactly one placeholder used by its section.")
        if len(placeholders) != len(set(placeholders)):
            raise ValueError("A section cannot repeat the same figure placeholder.")
        unknown = [key for key in placeholders if key not in catalogue]
        if unknown:
            raise ValueError(f"Unknown trace keys: {unknown}")
        without_placeholders = _PLACEHOLDER_RE.sub("", section.text_template)
        if _DIGIT_RE.search(without_placeholders):
            raise ValueError("Literal digits are forbidden; all figures must use trace placeholders.")

        rendered = section.text_template
        for key in placeholders:
            rendered = rendered.replace(f"{{{{{key}}}}}", catalogue[key].display_value)
            if key not in trace_order:
                trace_order.append(key)
        if "{{" in rendered or "}}" in rendered:
            raise ValueError("Malformed or unresolved figure placeholder.")
        rendered_sections.append(rendered.strip())

    traces = [
        FigureTrace(
            display_value=catalogue[key].display_value,
            report_path=key,
            raw_value=catalogue[key].raw_value,
        )
        for key in trace_order
    ]
    return "\n\n".join(rendered_sections), traces

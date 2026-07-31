from app.agent.classifier import DayFlag, DayType
from app.agent.facts import ApprovedFact
from app.agent.schemas import NarrativeDraft, NarrativeIntent
from app.agent.validation import required_fact_keys


def section(intent: NarrativeIntent, text_template: str, trace_keys: list[str]) -> dict:
    return {"intent": intent, "text_template": text_template, "trace_keys": trace_keys}


def build_fallback_draft(
    *,
    day_type: DayType,
    flags: frozenset[DayFlag],
    catalogue: dict[str, ApprovedFact],
) -> NarrativeDraft:
    sections: list[dict] = []
    if day_type == DayType.EMPTY:
        sections.append(section(
            NarrativeIntent.OVERVIEW,
            "Good evening. No billing activity, collections or refunds were recorded for {{metadata.business_date}}.",
            ["metadata.business_date"],
        ))
    elif day_type == DayType.REFUND_ONLY:
        refund_keys = ["reconciliation.refund_visit_count", "reconciliation.total_refunds_paise"]
        text = (
            "Good evening. No new sales were recorded today. "
            "{{reconciliation.refund_visit_count}} refunds totalled {{reconciliation.total_refunds_paise}}."
        )
        mode_keys = [key for key in catalogue if key.startswith("reconciliation.by_payment_mode.")]
        if mode_keys:
            text += " Refunds by payment mode: " + ", ".join(f"{{{{{key}}}}}" for key in mode_keys) + "."
            refund_keys.extend(mode_keys)
        sections.append(section(NarrativeIntent.REFUNDS, text, refund_keys))
    else:
        overview_keys = [
            "reconciliation.total_billed_paise",
            "ingestion.accepted_rows",
            "reconciliation.total_collected_paise",
            "reconciliation.total_outstanding_paise",
        ]
        text = (
            "Good evening. {{reconciliation.total_billed_paise}} was billed across "
            "{{ingestion.accepted_rows}} accepted rows, {{reconciliation.total_collected_paise}} was collected, "
            "and {{reconciliation.total_outstanding_paise}} remains outstanding."
        )
        if "reconciliation.collection_rate" in catalogue:
            text += " Collection rate was {{reconciliation.collection_rate}}."
            overview_keys.append("reconciliation.collection_rate")
        if "reconciliation.pending_visit_count" in required_fact_keys(day_type, flags, catalogue):
            text += " {{reconciliation.pending_visit_count}} visits still had outstanding balances."
            overview_keys.append("reconciliation.pending_visit_count")
        sections.append(section(NarrativeIntent.OVERVIEW, text, overview_keys))
        if day_type == DayType.SALES_AND_REFUNDS:
            sections.append(section(
                NarrativeIntent.REFUNDS,
                "Refunds totalled {{reconciliation.total_refunds_paise}}.",
                ["reconciliation.total_refunds_paise"],
            ))
        if "analytics.peak_hour.label" in catalogue:
            sections.append(section(
                NarrativeIntent.PEAK_HOUR,
                "The peak billing hour was {{analytics.peak_hour.label}}, with {{analytics.peak_hour.revenue_paise}} billed.",
                ["analytics.peak_hour.label", "analytics.peak_hour.revenue_paise"],
            ))
        if "analytics.top_medicines_by_quantity.0.drug_name" in catalogue:
            sections.append(section(
                NarrativeIntent.TOP_MEDICINE_QUANTITY,
                "{{analytics.top_medicines_by_quantity.0.drug_name}} led by quantity at {{analytics.top_medicines_by_quantity.0.quantity}} units.",
                ["analytics.top_medicines_by_quantity.0.drug_name", "analytics.top_medicines_by_quantity.0.quantity"],
            ))
        if "analytics.top_medicines_by_revenue.0.drug_name" in catalogue:
            sections.append(section(
                NarrativeIntent.TOP_MEDICINE_REVENUE,
                "{{analytics.top_medicines_by_revenue.0.drug_name}} led by gross medicine revenue at {{analytics.top_medicines_by_revenue.0.revenue_paise}}.",
                ["analytics.top_medicines_by_revenue.0.drug_name", "analytics.top_medicines_by_revenue.0.revenue_paise"],
            ))

    if DayFlag.PARTIAL_IMPORT in flags:
        sections.append(section(
            NarrativeIntent.IMPORT_QUALITY,
            "{{ingestion.accepted_rows}} rows were included and {{ingestion.rejected_rows}} rows were excluded after validation.",
            ["ingestion.accepted_rows", "ingestion.rejected_rows"],
        ))
    if DayFlag.HAS_DATA_QUALITY_WARNINGS in flags and "data_quality_warnings.0.message" in catalogue:
        sections.append(section(
            NarrativeIntent.DATA_QUALITY,
            "Data-quality note: {{data_quality_warnings.0.message}} Review the source data before merging medicine names.",
            ["data_quality_warnings.0.message"],
        ))

    unavailable = [] if day_type == DayType.EMPTY else [
        {"metric": "profit", "reason": "Cost prices were not provided in the billing data."}
    ]
    return NarrativeDraft(sections=sections, unavailable_metrics=unavailable)

import re
from dataclasses import dataclass
from enum import Enum

from app.agent.classifier import DayFlag, DayType
from app.agent.facts import ApprovedFact, FactKind
from app.agent.placeholders import PlaceholderError, extract_placeholders, render_template, validate_placeholders
from app.agent.schemas import NarrativeDraft, NarrativeIntent
from app.schemas.narrative import FigureTrace, UnavailableMetric


class ValidationCode(str, Enum):
    UNKNOWN_PLACEHOLDER = "UNKNOWN_PLACEHOLDER"
    MALFORMED_PLACEHOLDER = "MALFORMED_PLACEHOLDER"
    PLACEHOLDER_TRACE_MISMATCH = "PLACEHOLDER_TRACE_MISMATCH"
    TRACE_NOT_USED = "TRACE_NOT_USED"
    DUPLICATE_FACT_USAGE = "DUPLICATE_FACT_USAGE"
    INTENT_FACT_MISMATCH = "INTENT_FACT_MISMATCH"
    REQUIRED_FACT_MISSING = "REQUIRED_FACT_MISSING"
    PROHIBITED_FACT_USED = "PROHIBITED_FACT_USED"
    FACT_UNAVAILABLE = "FACT_UNAVAILABLE"
    LITERAL_NUMBER_FOUND = "LITERAL_NUMBER_FOUND"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    TEMPLATE_TOO_LONG = "TEMPLATE_TOO_LONG"
    OUTPUT_SCHEMA_INVALID = "OUTPUT_SCHEMA_INVALID"


class GroundingValidationError(ValueError):
    def __init__(self, codes: list[ValidationCode]):
        self.codes = sorted({code for code in codes}, key=lambda item: item.value)
        super().__init__(",".join(code.value for code in self.codes))


@dataclass(frozen=True, slots=True)
class RenderedNarrative:
    summary: str
    traces: list[FigureTrace]
    unavailable_metrics: list[UnavailableMetric]
    used_fact_keys: list[str]


UNAVAILABLE_METRICS = {
    "profit": "Cost prices were not provided in the billing data.",
}

INTENT_ALLOWED_PREFIXES: dict[NarrativeIntent, tuple[str, ...]] = {
    NarrativeIntent.OVERVIEW: (
        "metadata.business_date",
        "clinic.name",
        "reconciliation.total_billed_paise",
        "reconciliation.total_collected_paise",
        "reconciliation.total_outstanding_paise",
        "reconciliation.total_refunds_paise",
        "reconciliation.collection_rate",
        "reconciliation.pending_visit_count",
        "ingestion.accepted_rows",
    ),
    NarrativeIntent.COLLECTIONS: (
        "reconciliation.total_collected_paise",
        "reconciliation.total_billed_paise",
        "reconciliation.total_outstanding_paise",
        "reconciliation.collection_rate",
        "reconciliation.pending_visit_count",
    ),
    NarrativeIntent.REFUNDS: (
        "reconciliation.total_refunds_paise",
        "reconciliation.refund_visit_count",
        "reconciliation.by_payment_mode.",
    ),
    NarrativeIntent.PEAK_HOUR: ("analytics.peak_hour.",),
    NarrativeIntent.TOP_MEDICINE_QUANTITY: ("analytics.top_medicines_by_quantity.0.",),
    NarrativeIntent.TOP_MEDICINE_REVENUE: ("analytics.top_medicines_by_revenue.0.",),
    NarrativeIntent.IMPORT_QUALITY: ("ingestion.received_rows", "ingestion.accepted_rows", "ingestion.rejected_rows"),
    NarrativeIntent.DATA_QUALITY: ("data_quality_warnings.",),
    NarrativeIntent.UNAVAILABLE_METRIC: tuple(),
}

UNSUPPORTED_PATTERNS = [
    r"\bprofit(?:s|ed|ability)?\b",
    r"\bmargin(?:s)?\b",
    r"\bcost(?:s| price)?\b",
    r"\bgrowth\b|\bgrew\b|\bincrease(?:d)?\b|\bdecrease(?:d)?\b|\bdecline(?:d)?\b",
    r"\btrend(?:s|ing)?\b|\bforecast\b|\bpredict(?:ion|ed)?\b",
    r"\byesterday\b|\btarget\b|\bbest ever\b|\bworst ever\b|\babnormal\b|\bunusual\b",
    r"\binventory\b|\bstock(?:out)?\b|\bdiagnos(?:is|ed)\b|\bdoctor performance\b",
    r"\beffective(?:ness)?\b|\bfraud\b|\btax\b",
]
UNSUPPORTED_RE = re.compile("|".join(f"(?:{pattern})" for pattern in UNSUPPORTED_PATTERNS), re.IGNORECASE)
ASCII_OR_UNICODE_DIGIT_RE = re.compile(r"\d")
NUMBER_WORD_RE = re.compile(
    r"\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|lakh|crore)\b",
    re.IGNORECASE,
)


def required_fact_keys(day_type: DayType, flags: frozenset[DayFlag], catalogue: dict[str, ApprovedFact]) -> set[str]:
    if day_type == DayType.EMPTY:
        return {"metadata.business_date"}
    if day_type == DayType.REFUND_ONLY:
        keys = {"reconciliation.refund_visit_count", "reconciliation.total_refunds_paise"}
        keys.update(key for key in catalogue if key.startswith("reconciliation.by_payment_mode."))
    else:
        keys = {
            "reconciliation.total_billed_paise",
            "reconciliation.total_collected_paise",
            "reconciliation.total_outstanding_paise",
            "ingestion.accepted_rows",
        }
        if "reconciliation.collection_rate" in catalogue:
            keys.add("reconciliation.collection_rate")
        if day_type == DayType.SALES_AND_REFUNDS:
            keys.add("reconciliation.total_refunds_paise")
        if DayFlag.HAS_OUTSTANDING in flags:
            keys.add("reconciliation.pending_visit_count")
        if DayFlag.HAS_PEAK_HOUR in flags:
            keys.update({"analytics.peak_hour.label", "analytics.peak_hour.revenue_paise"})
        if DayFlag.HAS_MEDICINE_RANKINGS in flags:
            if "analytics.top_medicines_by_quantity.0.drug_name" in catalogue:
                keys.update({
                    "analytics.top_medicines_by_quantity.0.drug_name",
                    "analytics.top_medicines_by_quantity.0.quantity",
                })
            if "analytics.top_medicines_by_revenue.0.drug_name" in catalogue:
                keys.update({
                    "analytics.top_medicines_by_revenue.0.drug_name",
                    "analytics.top_medicines_by_revenue.0.revenue_paise",
                })
    if DayFlag.PARTIAL_IMPORT in flags:
        keys.update({"ingestion.accepted_rows", "ingestion.rejected_rows"})
    if DayFlag.HAS_DATA_QUALITY_WARNINGS in flags:
        keys.add("data_quality_warnings.0.message")
    return keys


def prohibited_intents(day_type: DayType) -> set[NarrativeIntent]:
    if day_type in {DayType.EMPTY, DayType.REFUND_ONLY}:
        return {
            NarrativeIntent.PEAK_HOUR,
            NarrativeIntent.TOP_MEDICINE_QUANTITY,
            NarrativeIntent.TOP_MEDICINE_REVENUE,
        }
    return set()


def _intent_allows(intent: NarrativeIntent, key: str) -> bool:
    return any(key == prefix or key.startswith(prefix) for prefix in INTENT_ALLOWED_PREFIXES[intent])


def _literal_text(template: str) -> str:
    return re.sub(r"\{\{[a-zA-Z0-9_.-]+\}\}", " ", template)


def _has_literal_number_claim(template: str, used_keys: list[str], catalogue: dict[str, ApprovedFact]) -> bool:
    literal = _literal_text(template)
    if ASCII_OR_UNICODE_DIGIT_RE.search(literal):
        digit_text_facts = [catalogue[key].display_value for key in used_keys if catalogue[key].kind == FactKind.TEXT]
        return not any(value and value in template for value in digit_text_facts)
    return bool(NUMBER_WORD_RE.search(literal))


def validate_draft(
    *,
    draft: NarrativeDraft,
    catalogue: dict[str, ApprovedFact],
    day_type: DayType,
    flags: frozenset[DayFlag],
    max_summary_length: int = 2_400,
) -> RenderedNarrative:
    codes: list[ValidationCode] = []
    used_fact_keys: list[str] = []
    rendered_sections: list[str] = []
    prohibited = prohibited_intents(day_type)

    if len({section.intent for section in draft.sections}) != len(draft.sections):
        codes.append(ValidationCode.OUTPUT_SCHEMA_INVALID)

    for section in draft.sections:
        if section.intent in prohibited:
            codes.append(ValidationCode.PROHIBITED_FACT_USED)
        try:
            placeholders = validate_placeholders(section.text_template, catalogue)
            declared = list(section.trace_keys)
            if len(declared) != len(set(declared)):
                codes.append(ValidationCode.DUPLICATE_FACT_USAGE)
            if set(placeholders) != set(declared):
                codes.append(ValidationCode.PLACEHOLDER_TRACE_MISMATCH)
            if any(key not in catalogue for key in declared):
                codes.append(ValidationCode.UNKNOWN_PLACEHOLDER)
            for key in placeholders:
                if not _intent_allows(section.intent, key):
                    codes.append(ValidationCode.INTENT_FACT_MISMATCH)
            if _has_literal_number_claim(section.text_template, placeholders, catalogue):
                codes.append(ValidationCode.LITERAL_NUMBER_FOUND)
            if UNSUPPORTED_RE.search(_literal_text(section.text_template)):
                codes.append(ValidationCode.UNSUPPORTED_CLAIM)
            rendered = render_template(section.text_template, catalogue)
            if rendered:
                rendered_sections.append(rendered)
            for key in placeholders:
                if key not in used_fact_keys:
                    used_fact_keys.append(key)
        except PlaceholderError as exc:
            codes.append(ValidationCode(exc.code) if exc.code in ValidationCode._value2member_map_ else ValidationCode.MALFORMED_PLACEHOLDER)

    missing = sorted(required_fact_keys(day_type, flags, catalogue) - set(used_fact_keys))
    if missing:
        codes.append(ValidationCode.REQUIRED_FACT_MISSING)

    unavailable = {item.metric.strip().lower(): item.reason.strip() for item in draft.unavailable_metrics}
    if day_type != DayType.EMPTY and unavailable.get("profit") is None:
        codes.append(ValidationCode.REQUIRED_FACT_MISSING)
    if any(metric not in UNAVAILABLE_METRICS for metric in unavailable):
        codes.append(ValidationCode.FACT_UNAVAILABLE)

    summary = "\n\n".join(rendered_sections).strip()
    if not summary or len(summary) > max_summary_length or "{{" in summary or "}}" in summary:
        codes.append(ValidationCode.TEMPLATE_TOO_LONG)

    if codes:
        raise GroundingValidationError(codes)

    traces = [
        FigureTrace(display_value=catalogue[key].display_value, report_path=catalogue[key].report_path, raw_value=catalogue[key].raw_value)
        for key in used_fact_keys
        if catalogue[key].traceable
    ]
    unavailable_metrics = [
        UnavailableMetric(metric="profit", reason=UNAVAILABLE_METRICS["profit"])
    ] if day_type != DayType.EMPTY else []
    return RenderedNarrative(
        summary=summary,
        traces=traces,
        unavailable_metrics=unavailable_metrics,
        used_fact_keys=used_fact_keys,
    )

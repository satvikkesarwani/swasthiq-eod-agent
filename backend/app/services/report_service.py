import logging
import hashlib
import json
from typing import Any

from app.core.limits import DEFAULT_MAX_MEDICINE_COMPARISONS_PER_REPORT, DEFAULT_MAX_MEDICINE_WARNINGS_PER_REPORT, MAX_SAFE_JSON_INTEGER
from app.schemas.ingestion import ValidatedVisit
from app.schemas.report import ActivityCounts, DataQualityWarning, DeterministicReport
from app.services.analytics_service import build_analytics
from app.services.reconciliation_service import build_reconciliation

logger = logging.getLogger(__name__)


def canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def build_source_hash_payload(
    *,
    clinic_id: str,
    business_date: str,
    clinic_name: str | None,
    clinic_location: str | None,
    records: list[Any],
) -> dict[str, Any]:
    return {
        "clinic_id": clinic_id,
        "business_date": business_date,
        "clinic_name": clinic_name,
        "clinic_location": clinic_location,
        "records": records,
    }


def build_report_hash_payload(
    *,
    clinic_id: str,
    business_date: str,
    accepted_rows: int,
    rejected_rows: int,
    report: DeterministicReport,
) -> dict[str, Any]:
    return {
        "clinic_id": clinic_id,
        "business_date": business_date,
        "accepted_rows": accepted_rows,
        "rejected_rows": rejected_rows,
        "report": report.model_dump(mode="json"),
    }


def _edit_distance_at_most_one(left: str, right: str) -> bool:
    if left == right:
        return False
    if abs(len(left) - len(right)) > 1:
        return False
    if len(left) > len(right):
        left, right = right, left
    if len(left) == len(right):
        return sum(a != b for a, b in zip(left, right, strict=True)) == 1
    index_left = index_right = differences = 0
    while index_left < len(left) and index_right < len(right):
        if left[index_left] == right[index_right]:
            index_left += 1
            index_right += 1
            continue
        differences += 1
        index_right += 1
        if differences > 1:
            return False
    return True


def build_activity_counts(visits: list[ValidatedVisit]) -> ActivityCounts:
    sale_visits = [visit for visit in visits if not visit.is_refund]
    refund_visits = [visit for visit in visits if visit.is_refund]
    return ActivityCounts(
        accepted_visit_count=len(visits),
        sale_visit_count=len(sale_visits),
        refund_visit_count=len(refund_visits),
        sale_line_item_count=sum(len(visit.line_items) for visit in sale_visits),
    )


def _candidate_key(name: str) -> tuple[str, int]:
    return (name[:2], len(name))


def build_data_quality_warnings(
    visits: list[ValidatedVisit],
    *,
    max_warnings: int = DEFAULT_MAX_MEDICINE_WARNINGS_PER_REPORT,
    max_comparisons: int = DEFAULT_MAX_MEDICINE_COMPARISONS_PER_REPORT,
) -> list[DataQualityWarning]:
    logger.info("analysis.quality.start visits=%s", len(visits))
    names = sorted(
        {
            item.drug_name_normalized
            for visit in visits
            for item in visit.line_items
            if not visit.is_refund
        }
    )
    warnings: list[DataQualityWarning] = []
    buckets: dict[tuple[str, int], list[str]] = {}
    for name in names:
        if len(name) < 5:
            continue
        for length in (len(name) - 1, len(name), len(name) + 1):
            buckets.setdefault((name[:2], length), []).append(name)

    comparisons = 0
    truncated = False
    seen_pairs: set[tuple[str, str]] = set()
    for name in names:
        for candidate in buckets.get(_candidate_key(name), []):
            left, right = sorted((name, candidate))
            if left == right or (left, right) in seen_pairs:
                continue
            seen_pairs.add((left, right))
            comparisons += 1
            if comparisons > max_comparisons:
                truncated = True
                break
            if _edit_distance_at_most_one(left, right):
                logger.warning("analysis.quality.warning possible_typo")
                if len(warnings) >= max_warnings:
                    truncated = True
                    break
                warnings.append(
                    DataQualityWarning(
                        code="POSSIBLE_MEDICINE_NAME_TYPO",
                        message="Possible medicine-name inconsistency detected.",
                        details={"names": [left, right], "action": "review_source_data"},
                    )
                )
        if truncated:
            break
    if truncated:
        warnings.append(
            DataQualityWarning(
                code="MEDICINE_WARNING_SCAN_TRUNCATED",
                message="Medicine-name warning scan reached configured safety limits.",
                details={"max_warnings": max_warnings, "max_comparisons": max_comparisons, "comparisons": comparisons},
            )
        )
    logger.info("analysis.quality.done medicine_names=%s warnings=%s comparisons=%s truncated=%s", len(names), len(warnings), comparisons, truncated)
    return warnings


def build_deterministic_report(
    visits: list[ValidatedVisit],
    *,
    max_medicine_warnings: int = DEFAULT_MAX_MEDICINE_WARNINGS_PER_REPORT,
    max_medicine_comparisons: int = DEFAULT_MAX_MEDICINE_COMPARISONS_PER_REPORT,
    max_safe_paise: int = MAX_SAFE_JSON_INTEGER,
) -> DeterministicReport:
    logger.info("analysis.report.start accepted_visits=%s", len(visits))
    activity_counts = build_activity_counts(visits)
    reconciliation = build_reconciliation(visits, max_safe_paise=max_safe_paise)
    analytics = build_analytics(visits, max_safe_paise=max_safe_paise)
    warnings = build_data_quality_warnings(
        visits,
        max_warnings=max_medicine_warnings,
        max_comparisons=max_medicine_comparisons,
    )
    report = DeterministicReport(
        activity_counts=activity_counts,
        reconciliation=reconciliation,
        analytics=analytics,
        data_quality_warnings=warnings,
    )
    logger.info(
        "analysis.report.done accepted_visits=%s sale_visits=%s refund_visits=%s top_quantity=%s top_revenue=%s warnings=%s",
        len(visits),
        activity_counts.sale_visit_count,
        activity_counts.refund_visit_count,
        len(analytics.top_medicines_by_quantity),
        len(analytics.top_medicines_by_revenue),
        len(warnings),
    )
    return DeterministicReport.model_validate(report.model_dump(mode="json"))

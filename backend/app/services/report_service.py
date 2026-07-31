import logging
import hashlib
import json
from itertools import combinations
from typing import Any

from app.schemas.ingestion import ValidatedVisit
from app.schemas.report import DataQualityWarning, DeterministicReport
from app.services.analytics_service import build_analytics
from app.services.reconciliation_service import build_reconciliation

logger = logging.getLogger(__name__)


def canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
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


def build_data_quality_warnings(visits: list[ValidatedVisit]) -> list[DataQualityWarning]:
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
    for left, right in combinations(names, 2):
        if _edit_distance_at_most_one(left, right):
            logger.warning("analysis.quality.warning possible_typo left=%s right=%s", left, right)
            warnings.append(
                DataQualityWarning(
                    code="POSSIBLE_MEDICINE_NAME_TYPO",
                    message=f"Possible medicine-name inconsistency: {left} / {right}.",
                    details={"names": [left, right], "action": "review_source_data"},
                )
            )
    logger.info("analysis.quality.done medicine_names=%s warnings=%s", len(names), len(warnings))
    return warnings


def build_deterministic_report(visits: list[ValidatedVisit]) -> DeterministicReport:
    logger.info("analysis.report.start accepted_visits=%s", len(visits))
    reconciliation = build_reconciliation(visits)
    analytics = build_analytics(visits)
    warnings = build_data_quality_warnings(visits)
    logger.info(
        "analysis.report.done accepted_visits=%s total_billed=%s total_collected=%s top_quantity=%s top_revenue=%s warnings=%s",
        len(visits),
        reconciliation.total_billed_paise,
        reconciliation.total_collected_paise,
        len(analytics.top_medicines_by_quantity),
        len(analytics.top_medicines_by_revenue),
        len(warnings),
    )
    return DeterministicReport(
        reconciliation=reconciliation,
        analytics=analytics,
        data_quality_warnings=warnings,
    )

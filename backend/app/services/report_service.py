import hashlib
import json
from itertools import combinations
from typing import Any

from app.schemas.ingestion import ValidatedVisit
from app.schemas.report import DataQualityWarning, DeterministicReport
from app.services.analytics_service import build_analytics
from app.services.reconciliation_service import build_reconciliation


def canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


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
            warnings.append(
                DataQualityWarning(
                    code="POSSIBLE_MEDICINE_NAME_TYPO",
                    message=f"Possible medicine-name inconsistency: {left} / {right}.",
                    details={"names": [left, right], "action": "review_source_data"},
                )
            )
    return warnings


def build_deterministic_report(visits: list[ValidatedVisit]) -> DeterministicReport:
    return DeterministicReport(
        reconciliation=build_reconciliation(visits),
        analytics=build_analytics(visits),
        data_quality_warnings=build_data_quality_warnings(visits),
    )

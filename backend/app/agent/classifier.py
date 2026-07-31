from enum import Enum
from typing import Any


class DayType(str, Enum):
    EMPTY = "empty"
    REFUND_ONLY = "refund_only"
    SALES_ONLY = "sales_only"
    SALES_AND_REFUNDS = "sales_and_refunds"


class DayFlag(str, Enum):
    HAS_OUTSTANDING = "has_outstanding"
    PARTIAL_IMPORT = "partial_import"
    HAS_DATA_QUALITY_WARNINGS = "has_data_quality_warnings"
    HAS_PEAK_HOUR = "has_peak_hour"
    HAS_MEDICINE_RANKINGS = "has_medicine_rankings"


def classify_day(*, clinic_day: Any) -> tuple[DayType, frozenset[DayFlag]]:
    report = clinic_day.report_json
    reconciliation = report["reconciliation"]
    analytics = report["analytics"]
    activity_counts = report.get("activity_counts")
    if isinstance(activity_counts, dict):
        has_sales = activity_counts.get("sale_visit_count", 0) > 0 or activity_counts.get("sale_line_item_count", 0) > 0
        has_refunds = activity_counts.get("refund_visit_count", reconciliation.get("refund_visit_count", 0)) > 0
    else:
        has_sales = reconciliation["total_billed_paise"] > 0
        has_refunds = reconciliation["refund_visit_count"] > 0 and reconciliation["total_refunds_paise"] > 0

    if not has_sales and not has_refunds:
        day_type = DayType.EMPTY
    elif not has_sales:
        day_type = DayType.REFUND_ONLY
    elif has_refunds:
        day_type = DayType.SALES_AND_REFUNDS
    else:
        day_type = DayType.SALES_ONLY

    flags: set[DayFlag] = set()
    if reconciliation["total_outstanding_paise"] > 0:
        flags.add(DayFlag.HAS_OUTSTANDING)
    if clinic_day.accepted_rows > 0 and clinic_day.rejected_rows > 0:
        flags.add(DayFlag.PARTIAL_IMPORT)
    if report.get("data_quality_warnings"):
        flags.add(DayFlag.HAS_DATA_QUALITY_WARNINGS)
    if analytics.get("peak_hour"):
        flags.add(DayFlag.HAS_PEAK_HOUR)
    if analytics.get("top_medicines_by_quantity") or analytics.get("top_medicines_by_revenue"):
        flags.add(DayFlag.HAS_MEDICINE_RANKINGS)
    return day_type, frozenset(flags)

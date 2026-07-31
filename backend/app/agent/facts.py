from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.money import format_hour_range, format_paise, format_rate


class FactKind(str, Enum):
    MONEY = "money"
    COUNT = "count"
    PERCENTAGE = "percentage"
    HOUR_RANGE = "hour_range"
    TEXT = "text"
    DATE = "date"
    STATUS = "status"


class ApprovedFact(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    report_path: str
    label: str
    kind: FactKind
    raw_value: int | float | str | dict[str, int] | None
    display_value: str
    traceable: bool = True


def format_count(value: int) -> str:
    return str(value)


def format_date(value: Any) -> str:
    return value.strftime("%d %b %Y")


def format_text(value: str | None) -> str:
    return (value or "").strip()


def _append(catalogue: dict[str, ApprovedFact], fact: ApprovedFact) -> None:
    catalogue[fact.key] = fact


def build_fact_catalogue(*, clinic_day: Any) -> dict[str, ApprovedFact]:
    report = clinic_day.report_json
    reconciliation = report["reconciliation"]
    analytics = report["analytics"]
    catalogue: dict[str, ApprovedFact] = {}

    clinic_name = getattr(clinic_day, "clinic_name", None)
    if clinic_name:
        _append(catalogue, ApprovedFact(
            key="clinic.name", report_path="clinic.name", label="Clinic name",
            kind=FactKind.TEXT, raw_value=clinic_name, display_value=format_text(clinic_name),
        ))
    _append(catalogue, ApprovedFact(
        key="metadata.business_date", report_path="metadata.business_date", label="Business date",
        kind=FactKind.DATE, raw_value=clinic_day.business_date.isoformat(), display_value=format_date(clinic_day.business_date),
    ))
    for key, value, label in [
        ("ingestion.received_rows", getattr(clinic_day, "received_rows", clinic_day.accepted_rows + clinic_day.rejected_rows), "Received rows"),
        ("ingestion.accepted_rows", clinic_day.accepted_rows, "Accepted rows"),
        ("ingestion.rejected_rows", clinic_day.rejected_rows, "Rejected rows"),
    ]:
        _append(catalogue, ApprovedFact(
            key=key, report_path=key, label=label, kind=FactKind.COUNT,
            raw_value=value, display_value=format_count(value),
        ))

    money_fields = [
        ("reconciliation.total_billed_paise", "Total billed"),
        ("reconciliation.total_collected_paise", "Total collected"),
        ("reconciliation.total_outstanding_paise", "Total outstanding"),
        ("reconciliation.total_refunds_paise", "Total refunds"),
        ("reconciliation.total_discount_paise", "Total discount"),
    ]
    for key, label in money_fields:
        field = key.split(".")[-1]
        value = reconciliation[field]
        _append(catalogue, ApprovedFact(
            key=key, report_path=key, label=label, kind=FactKind.MONEY,
            raw_value=value, display_value=format_paise(value),
        ))

    if reconciliation["collection_rate"] is not None:
        _append(catalogue, ApprovedFact(
            key="reconciliation.collection_rate", report_path="reconciliation.collection_rate",
            label="Collection rate", kind=FactKind.PERCENTAGE,
            raw_value=reconciliation["collection_rate"], display_value=format_rate(reconciliation["collection_rate"]),
        ))
    for key, value, label in [
        ("reconciliation.pending_visit_count", reconciliation["pending_visit_count"], "Pending visits"),
        ("reconciliation.refund_visit_count", reconciliation["refund_visit_count"], "Refund visits"),
    ]:
        _append(catalogue, ApprovedFact(
            key=key, report_path=key, label=label, kind=FactKind.COUNT,
            raw_value=value, display_value=format_count(value),
        ))

    for mode in ("cash", "card", "upi"):
        metrics = reconciliation["by_payment_mode"].get(mode)
        if metrics and metrics.get("refunds_paise", 0) > 0:
            key = f"reconciliation.by_payment_mode.{mode}.refunds_paise"
            _append(catalogue, ApprovedFact(
                key=key, report_path=key, label=f"{mode.upper()} refunds", kind=FactKind.MONEY,
                raw_value=metrics["refunds_paise"], display_value=format_paise(metrics["refunds_paise"]),
            ))

    peak = analytics.get("peak_hour")
    if peak:
        _append(catalogue, ApprovedFact(
            key="analytics.peak_hour.label", report_path="analytics.peak_hour",
            label="Peak billing hour", kind=FactKind.HOUR_RANGE,
            raw_value={"start_hour_utc": peak["start_hour_utc"], "end_hour_utc": peak["end_hour_utc"]},
            display_value=format_hour_range(peak["start_hour_utc"], peak["end_hour_utc"]),
        ))
        _append(catalogue, ApprovedFact(
            key="analytics.peak_hour.revenue_paise", report_path="analytics.peak_hour.revenue_paise",
            label="Peak-hour billed revenue", kind=FactKind.MONEY,
            raw_value=peak["revenue_paise"], display_value=format_paise(peak["revenue_paise"]),
        ))

    for index, item in enumerate(analytics.get("top_medicines_by_quantity", [])):
        prefix = f"analytics.top_medicines_by_quantity.{index}"
        _append(catalogue, ApprovedFact(
            key=f"{prefix}.drug_name", report_path=f"{prefix}.drug_name", label=f"Quantity rank {index + 1} medicine",
            kind=FactKind.TEXT, raw_value=item["drug_name"], display_value=format_text(item["drug_name"]),
        ))
        _append(catalogue, ApprovedFact(
            key=f"{prefix}.quantity", report_path=f"{prefix}.quantity", label=f"Quantity rank {index + 1} units",
            kind=FactKind.COUNT, raw_value=item["quantity"], display_value=format_count(item["quantity"]),
        ))
    for index, item in enumerate(analytics.get("top_medicines_by_revenue", [])):
        prefix = f"analytics.top_medicines_by_revenue.{index}"
        _append(catalogue, ApprovedFact(
            key=f"{prefix}.drug_name", report_path=f"{prefix}.drug_name", label=f"Revenue rank {index + 1} medicine",
            kind=FactKind.TEXT, raw_value=item["drug_name"], display_value=format_text(item["drug_name"]),
        ))
        _append(catalogue, ApprovedFact(
            key=f"{prefix}.revenue_paise", report_path=f"{prefix}.revenue_paise", label=f"Revenue rank {index + 1} amount",
            kind=FactKind.MONEY, raw_value=item["revenue_paise"], display_value=format_paise(item["revenue_paise"]),
        ))

    for index, warning in enumerate(report.get("data_quality_warnings", [])):
        _append(catalogue, ApprovedFact(
            key=f"data_quality_warnings.{index}.message", report_path=f"data_quality_warnings.{index}.message",
            label=f"Data-quality warning {index + 1}", kind=FactKind.TEXT,
            raw_value=warning["message"], display_value=format_text(warning["message"]),
        ))
    return dict(sorted(catalogue.items()))

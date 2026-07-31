from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator


class PaymentModeMetrics(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    billed_paise: StrictInt = 0
    collected_paise: StrictInt = 0
    outstanding_paise: StrictInt = 0
    refunds_paise: StrictInt = 0


class ActivityCounts(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    accepted_visit_count: StrictInt = Field(ge=0)
    sale_visit_count: StrictInt = Field(ge=0)
    refund_visit_count: StrictInt = Field(ge=0)
    sale_line_item_count: StrictInt = Field(ge=0)


class ReconciliationReport(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    total_billed_paise: StrictInt
    total_collected_paise: StrictInt
    total_outstanding_paise: StrictInt
    total_refunds_paise: StrictInt
    total_discount_paise: StrictInt
    collection_rate: float | None
    collection_rate_basis_points: StrictInt | None = None
    pending_visit_count: StrictInt
    refund_visit_count: StrictInt
    by_payment_mode: dict[str, PaymentModeMetrics]


class HourlyRevenue(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    hour_utc: StrictInt = Field(ge=0, le=23)
    revenue_paise: StrictInt


class PeakHour(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    start_hour_utc: StrictInt
    end_hour_utc: StrictInt
    revenue_paise: StrictInt


class MedicineQuantityRanking(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    rank: StrictInt
    drug_name: str
    quantity: StrictInt


class MedicineRevenueRanking(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    rank: StrictInt
    drug_name: str
    revenue_paise: StrictInt


class AnalyticsReport(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    revenue_by_hour: list[HourlyRevenue]
    peak_hour: PeakHour | None
    top_medicines_by_quantity: list[MedicineQuantityRanking]
    top_medicines_by_revenue: list[MedicineRevenueRanking]


class DataQualityWarning(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class DeterministicReport(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    activity_counts: ActivityCounts
    reconciliation: ReconciliationReport
    analytics: AnalyticsReport
    data_quality_warnings: list[DataQualityWarning]

    @model_validator(mode="after")
    def validate_report_invariants(self) -> "DeterministicReport":
        if sum(row.revenue_paise for row in self.analytics.revenue_by_hour) != self.reconciliation.total_billed_paise:
            raise ValueError("hourly revenue must equal total billed paise")
        mode_totals = self.reconciliation.by_payment_mode.values()
        if sum(item.billed_paise for item in mode_totals) != self.reconciliation.total_billed_paise:
            raise ValueError("payment-mode billed totals must equal total billed paise")
        mode_totals = self.reconciliation.by_payment_mode.values()
        if sum(item.collected_paise for item in mode_totals) != self.reconciliation.total_collected_paise:
            raise ValueError("payment-mode collected totals must equal total collected paise")
        mode_totals = self.reconciliation.by_payment_mode.values()
        if sum(item.outstanding_paise for item in mode_totals) != self.reconciliation.total_outstanding_paise:
            raise ValueError("payment-mode outstanding totals must equal total outstanding paise")
        mode_totals = self.reconciliation.by_payment_mode.values()
        if sum(item.refunds_paise for item in mode_totals) != self.reconciliation.total_refunds_paise:
            raise ValueError("payment-mode refund totals must equal total refunds paise")
        if self.activity_counts.refund_visit_count != self.reconciliation.refund_visit_count:
            raise ValueError("activity refund count must match reconciliation refund count")
        return self


class IngestionSummary(BaseModel):
    received_rows: int
    accepted_rows: int
    rejected_rows: int
    total_issue_count: int = 0
    returned_issue_count: int = 0
    issues_truncated: bool = False
    errors: list[dict[str, Any]] = Field(default_factory=list)


class IngestionIssue(BaseModel):
    row_index: int
    visit_id: str | None = None
    field_path: str | None = None
    error_code: str
    message: str


class IngestionIssueListResponse(BaseModel):
    clinic_id: str
    business_date: date
    count: int
    limit: int
    offset: int
    errors: list[IngestionIssue]


class ClinicDayResponse(BaseModel):
    clinic_id: str
    clinic_name: str | None
    clinic_location: str | None
    business_date: date
    operation: str | None = None
    status: str
    ingestion: IngestionSummary
    report: DeterministicReport
    source_hash: str
    report_hash: str
    narrative_status: str
    created_at: datetime
    updated_at: datetime


class ClinicDayListItem(BaseModel):
    clinic_id: str
    clinic_name: str | None
    business_date: date
    status: str
    accepted_rows: int
    rejected_rows: int
    total_billed_paise: int
    total_collected_paise: int
    total_outstanding_paise: int
    total_refunds_paise: int
    report_hash: str
    narrative_status: str
    updated_at: datetime


class ClinicDayListResponse(BaseModel):
    items: list[ClinicDayListItem]
    limit: int
    offset: int
    count: int


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


class ErrorDetail(BaseModel):
    field: str | None = None
    code: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody

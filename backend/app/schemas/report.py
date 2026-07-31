from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class PaymentModeMetrics(BaseModel):
    billed_paise: int = 0
    collected_paise: int = 0
    outstanding_paise: int = 0
    refunds_paise: int = 0


class ReconciliationReport(BaseModel):
    total_billed_paise: int
    total_collected_paise: int
    total_outstanding_paise: int
    total_refunds_paise: int
    total_discount_paise: int
    collection_rate: float | None
    pending_visit_count: int
    refund_visit_count: int
    by_payment_mode: dict[str, PaymentModeMetrics]


class HourlyRevenue(BaseModel):
    hour_utc: int = Field(ge=0, le=23)
    revenue_paise: int


class PeakHour(BaseModel):
    start_hour_utc: int
    end_hour_utc: int
    revenue_paise: int


class MedicineQuantityRanking(BaseModel):
    rank: int
    drug_name: str
    quantity: int


class MedicineRevenueRanking(BaseModel):
    rank: int
    drug_name: str
    revenue_paise: int


class AnalyticsReport(BaseModel):
    revenue_by_hour: list[HourlyRevenue]
    peak_hour: PeakHour | None
    top_medicines_by_quantity: list[MedicineQuantityRanking]
    top_medicines_by_revenue: list[MedicineRevenueRanking]


class DataQualityWarning(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class DeterministicReport(BaseModel):
    reconciliation: ReconciliationReport
    analytics: AnalyticsReport
    data_quality_warnings: list[DataQualityWarning]


class IngestionSummary(BaseModel):
    received_rows: int
    accepted_rows: int
    rejected_rows: int
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

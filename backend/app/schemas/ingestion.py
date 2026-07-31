from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentMode(StrEnum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"


class BillingLogRequest(BaseModel):
    records: list[Any] = Field(description="Submitted clinic-day billing rows. May be empty for a valid no-activity day.")
    clinic_name: str | None = Field(default=None, min_length=1, max_length=200, description="Optional clinic display name.")
    clinic_location: str | None = Field(default=None, min_length=1, max_length=300, description="Optional clinic location.")


class LineItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    drug_name: str = Field(min_length=1, max_length=200)
    qty: int = Field(gt=0, le=100_000)
    unit_price_paise: int = Field(ge=0, le=1_000_000_000)


class BillingVisitInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    clinic_id: str = Field(min_length=1, max_length=100)
    visit_id: str = Field(min_length=1, max_length=120)
    timestamp: datetime
    doctor_id: str = Field(min_length=1, max_length=120)
    line_items: list[LineItemInput] = Field(min_length=1, max_length=1_000)
    payment_mode: PaymentMode
    amount_paid_paise: int = Field(ge=-1_000_000_000, le=1_000_000_000)
    discount_paise: int = Field(ge=0, le=1_000_000_000)
    is_refund: bool

    @field_validator("timestamp")
    @classmethod
    def require_utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a UTC timezone offset")
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("timestamp must be UTC (Z or +00:00)")
        return value.astimezone(timezone.utc)


class NormalizedLineItem(BaseModel):
    drug_name_source: str
    drug_name_normalized: str
    qty: int
    unit_price_paise: int
    gross_revenue_paise: int


class ValidatedVisit(BaseModel):
    clinic_id: str
    visit_id: str
    timestamp: datetime
    doctor_id: str
    line_items: list[NormalizedLineItem]
    payment_mode: PaymentMode
    amount_paid_paise: int
    discount_paise: int
    is_refund: bool
    gross_line_total_paise: int
    billed_paise: int
    outstanding_paise: int


class RowIssue(BaseModel):
    row_index: int
    visit_id: str | None = None
    field: str
    code: str
    message: str
    raw_row: dict[str, Any] | None = None


class IngestionResult(BaseModel):
    clinic_id: str
    business_date: date
    received_rows: int
    accepted: list[ValidatedVisit]
    rejected: list[RowIssue]

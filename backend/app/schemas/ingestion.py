from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictBool, conint, field_validator, model_validator

from app.core.limits import (
    MAX_AMOUNT_PAID_PAISE,
    MAX_CLINIC_LOCATION_LENGTH,
    MAX_CLINIC_NAME_LENGTH,
    MAX_DOCTOR_ID_LENGTH,
    MAX_DRUG_NAME_LENGTH,
    MAX_LINE_ITEMS_PER_RECORD,
    MAX_QTY_PER_LINE_ITEM,
    MAX_UNIT_PRICE_PAISE,
    MAX_VISIT_ID_LENGTH,
    MAX_DISCOUNT_PAISE,
)
from app.core.safe_strings import has_control_character


class PaymentMode(StrEnum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"


class BillingLogRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", str_strip_whitespace=True)

    records: list[Any] = Field(description="Submitted clinic-day billing rows. May be empty for a valid no-activity day.")
    clinic_name: str | None = Field(default=None, min_length=1, max_length=MAX_CLINIC_NAME_LENGTH, description="Optional clinic display name.")
    clinic_location: str | None = Field(default=None, min_length=1, max_length=MAX_CLINIC_LOCATION_LENGTH, description="Optional clinic location.")

    @field_validator("clinic_name", "clinic_location", mode="before")
    @classmethod
    def strict_optional_metadata_string(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("metadata field must be a string")
        cleaned = value.strip()
        return cleaned or None

    @field_validator("clinic_name", "clinic_location")
    @classmethod
    def metadata_no_control_characters(cls, value: str | None) -> str | None:
        if value is not None and has_control_character(value):
            raise ValueError("control characters are not allowed")
        return value


class LineItemInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", str_strip_whitespace=True)

    drug_name: str = Field(min_length=1, max_length=MAX_DRUG_NAME_LENGTH)
    qty: conint(strict=True, gt=0, le=MAX_QTY_PER_LINE_ITEM)
    unit_price_paise: conint(strict=True, ge=0, le=MAX_UNIT_PRICE_PAISE)

    @field_validator("drug_name")
    @classmethod
    def drug_name_no_control_characters(cls, value: str) -> str:
        if has_control_character(value):
            raise ValueError("control characters are not allowed")
        return value


class BillingVisitInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", str_strip_whitespace=True)

    clinic_id: str = Field(min_length=1, max_length=100)
    visit_id: str = Field(min_length=1, max_length=MAX_VISIT_ID_LENGTH)
    timestamp: datetime
    doctor_id: str = Field(min_length=1, max_length=MAX_DOCTOR_ID_LENGTH)
    line_items: list[LineItemInput] = Field(min_length=1, max_length=MAX_LINE_ITEMS_PER_RECORD)
    payment_mode: PaymentMode
    amount_paid_paise: conint(strict=True, ge=-MAX_AMOUNT_PAID_PAISE, le=MAX_AMOUNT_PAID_PAISE)
    discount_paise: conint(strict=True, ge=0, le=MAX_DISCOUNT_PAISE)
    is_refund: StrictBool

    @field_validator("clinic_id", "visit_id", "doctor_id")
    @classmethod
    def identifiers_no_control_characters(cls, value: str) -> str:
        if has_control_character(value):
            raise ValueError("control characters are not allowed")
        return value

    @field_validator("payment_mode", mode="before")
    @classmethod
    def parse_payment_mode_string(cls, value: object) -> PaymentMode:
        if not isinstance(value, str):
            raise ValueError("payment_mode must be a string")
        try:
            return PaymentMode(value)
        except ValueError as exc:
            raise ValueError("payment_mode must be cash, card, or upi") from exc

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_iso_timestamp_only(cls, value: object) -> datetime:
        if not isinstance(value, str):
            raise ValueError("timestamp must be an ISO 8601 string")
        candidate = value.strip()
        if not candidate:
            raise ValueError("timestamp must not be blank")
        normalized = candidate.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError("timestamp must be a valid ISO 8601 string") from exc

    @field_validator("timestamp")
    @classmethod
    def require_utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a UTC timezone offset")
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("timestamp must be UTC (Z or +00:00)")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def enforce_dynamic_line_item_limit(self) -> "BillingVisitInput":
        if len(self.line_items) > MAX_LINE_ITEMS_PER_RECORD:
            raise ValueError("too many line items")
        return self


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
    total_issue_count: int
    returned_issue_count: int
    issues_truncated: bool

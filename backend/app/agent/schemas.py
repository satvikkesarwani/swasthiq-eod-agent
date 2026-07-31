from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NarrativeIntent(str, Enum):
    OVERVIEW = "overview"
    COLLECTIONS = "collections"
    REFUNDS = "refunds"
    PEAK_HOUR = "peak_hour"
    TOP_MEDICINE_QUANTITY = "top_medicine_quantity"
    TOP_MEDICINE_REVENUE = "top_medicine_revenue"
    IMPORT_QUALITY = "import_quality"
    DATA_QUALITY = "data_quality"
    UNAVAILABLE_METRIC = "unavailable_metric"


class NarrativeSectionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    intent: NarrativeIntent
    text_template: str = Field(min_length=1, max_length=1_500)
    trace_keys: list[str] = Field(min_length=1, max_length=30)


class UnavailableMetricDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metric: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)


class NarrativeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sections: list[NarrativeSectionDraft] = Field(min_length=1, max_length=8)
    unavailable_metrics: list[UnavailableMetricDraft] = Field(max_length=10)


class NarrativeGenerationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clinic_id: str
    clinic_name: str | None = None
    clinic_location: str | None = None
    business_date: str
    report_hash: str
    day_type: str | None = None
    flags: list[str] = Field(default_factory=list)
    accepted_rows: int
    rejected_rows: int
    report: dict[str, Any]
    approved_placeholders: dict[str, str]
    mandatory_fact_keys: list[str] = Field(default_factory=list)
    prohibited_intents: list[str] = Field(default_factory=list)
    repair_feedback: list[str] = Field(default_factory=list)
    invalid_draft: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class NarrativeProviderResult:
    candidate: NarrativeDraft
    provider: str
    model: str | None
    generation_ms: int

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NarrativeSectionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

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
    accepted_rows: int
    rejected_rows: int
    report: dict[str, Any]
    approved_placeholders: dict[str, str]


@dataclass(frozen=True, slots=True)
class NarrativeProviderResult:
    candidate: NarrativeDraft
    provider: str
    model: str | None
    generation_ms: int


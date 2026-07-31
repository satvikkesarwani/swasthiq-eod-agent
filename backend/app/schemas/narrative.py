from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NarrativeGenerateRequest(BaseModel):
    force_regenerate: bool = False


class NarrativeSectionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text_template: str = Field(min_length=1, max_length=1_500)
    trace_keys: list[str] = Field(max_length=30)


class UnavailableMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)


class NarrativeCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sections: list[NarrativeSectionCandidate] = Field(min_length=1, max_length=8)
    unavailable_metrics: list[UnavailableMetric] = Field(max_length=10)


class FigureTrace(BaseModel):
    display_value: str
    report_path: str
    raw_value: Any


class NarrativeResponse(BaseModel):
    status: str
    summary: str
    traces: list[FigureTrace]
    unavailable_metrics: list[UnavailableMetric]
    report_hash: str
    provider: str | None = None
    model: str | None = None

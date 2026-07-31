import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.agent.facts import build_fact_catalogue
from app.agent.placeholders import render_template
from app.core.money import format_hour_range, format_paise, format_rate
from app.schemas.narrative import FigureTrace, NarrativeCandidate

_PLACEHOLDER_RE = re.compile(r"\{\{([a-zA-Z0-9_.-]+)\}\}")
_DIGIT_RE = re.compile(r"\d")


@dataclass(frozen=True, slots=True)
class TraceValue:
    raw_value: Any
    display_value: str


def build_trace_catalogue(*, clinic_day: Any) -> dict[str, TraceValue]:
    return {
        key: TraceValue(raw_value=fact.raw_value, display_value=fact.display_value)
        for key, fact in build_fact_catalogue(clinic_day=clinic_day).items()
    }


def validate_and_render_candidate(
    candidate: NarrativeCandidate, catalogue: dict[str, TraceValue]
) -> tuple[str, list[FigureTrace]]:
    rendered_sections: list[str] = []
    trace_order: list[str] = []

    for section in candidate.sections:
        placeholders = _PLACEHOLDER_RE.findall(section.text_template)
        if set(placeholders) != set(section.trace_keys):
            raise ValueError("Each trace_key must match exactly one placeholder used by its section.")
        if len(placeholders) != len(set(placeholders)):
            raise ValueError("A section cannot repeat the same figure placeholder.")
        unknown = [key for key in placeholders if key not in catalogue]
        if unknown:
            raise ValueError(f"Unknown trace keys: {unknown}")
        without_placeholders = _PLACEHOLDER_RE.sub("", section.text_template)
        if _DIGIT_RE.search(without_placeholders):
            raise ValueError("Literal digits are forbidden; all figures must use trace placeholders.")

        rendered = section.text_template
        for key in placeholders:
            rendered = rendered.replace(f"{{{{{key}}}}}", catalogue[key].display_value)
            if key not in trace_order:
                trace_order.append(key)
        if "{{" in rendered or "}}" in rendered:
            raise ValueError("Malformed or unresolved figure placeholder.")
        rendered_sections.append(rendered.strip())

    traces = [
        FigureTrace(
            display_value=catalogue[key].display_value,
            report_path=key,
            raw_value=catalogue[key].raw_value,
        )
        for key in trace_order
    ]
    return "\n\n".join(rendered_sections), traces

import json
from typing import Any

from app.agent.schemas import NarrativeGenerationInput
from app.services.trace_service import TraceValue


def build_narrative_generation_input(*, clinic_day: Any, catalogue: dict[str, TraceValue]) -> NarrativeGenerationInput:
    report = clinic_day.report_json
    return NarrativeGenerationInput(
        clinic_id=clinic_day.clinic_id,
        clinic_name=clinic_day.clinic_name,
        clinic_location=clinic_day.clinic_location,
        business_date=clinic_day.business_date.isoformat(),
        report_hash=clinic_day.report_hash,
        accepted_rows=clinic_day.accepted_rows,
        rejected_rows=clinic_day.rejected_rows,
        report=report,
        approved_placeholders={key: value.display_value for key, value in sorted(catalogue.items())},
    )


def serialize_generation_input(model_input: NarrativeGenerationInput) -> tuple[str, str]:
    context = model_input.model_dump(mode="json", exclude={"approved_placeholders"})
    return (
        json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        json.dumps(model_input.approved_placeholders, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )


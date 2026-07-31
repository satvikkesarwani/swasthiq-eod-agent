import json
from typing import Any

from app.agent.classifier import classify_day
from app.agent.facts import ApprovedFact
from app.agent.schemas import NarrativeGenerationInput
from app.agent.validation import prohibited_intents, required_fact_keys


def build_narrative_generation_input(*, clinic_day: Any, catalogue: dict[str, ApprovedFact]) -> NarrativeGenerationInput:
    report = clinic_day.report_json
    day_type, flags = classify_day(clinic_day=clinic_day)
    return NarrativeGenerationInput(
        clinic_id=clinic_day.clinic_id,
        clinic_name=clinic_day.clinic_name,
        clinic_location=clinic_day.clinic_location,
        business_date=clinic_day.business_date.isoformat(),
        report_hash=clinic_day.report_hash,
        day_type=day_type.value,
        flags=sorted(flag.value for flag in flags),
        accepted_rows=clinic_day.accepted_rows,
        rejected_rows=clinic_day.rejected_rows,
        report=report,
        approved_placeholders={key: value.display_value for key, value in sorted(catalogue.items())},
        mandatory_fact_keys=sorted(required_fact_keys(day_type, flags, catalogue)),
        prohibited_intents=sorted(intent.value for intent in prohibited_intents(day_type)),
    )


def serialize_generation_input(model_input: NarrativeGenerationInput) -> tuple[str, str]:
    context = model_input.model_dump(mode="json", exclude={"approved_placeholders", "invalid_draft"})
    return (
        json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        json.dumps(model_input.approved_placeholders, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )

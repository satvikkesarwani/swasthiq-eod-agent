import asyncio
import json

import pytest
from langchain_core.runnables import RunnableLambda
from pydantic import SecretStr, ValidationError

from app.agent.context import build_narrative_generation_input, serialize_generation_input
from app.agent.exceptions import (
    NarrativeProviderAuthenticationError,
    NarrativeProviderInvalidResponse,
    NarrativeProviderNotConfigured,
    NarrativeProviderRateLimited,
    NarrativeProviderTimeout,
    NarrativeProviderUnavailable,
)
from app.agent.nvidia_client import ChatNVIDIANarrativeProvider, classify_provider_exception
from app.agent.schemas import NarrativeDraft, NarrativeGenerationInput
from app.services.trace_service import build_trace_catalogue


def generation_input() -> NarrativeGenerationInput:
    return NarrativeGenerationInput(
        clinic_id="CLN-001",
        clinic_name="SwasthiQ",
        clinic_location="Indore",
        business_date="2026-07-27",
        report_hash="sha256:" + "a" * 64,
        accepted_rows=1,
        rejected_rows=0,
        report={"reconciliation": {"total_billed_paise": 1000}, "analytics": {"peak_hour": None}},
        approved_placeholders={"reconciliation.total_billed_paise": "₹10"},
    )


def valid_draft() -> NarrativeDraft:
    return NarrativeDraft(
        sections=[
            {
                "text_template": "Billed {{reconciliation.total_billed_paise}}.",
                "trace_keys": ["reconciliation.total_billed_paise"],
            }
        ],
        unavailable_metrics=[
            {"metric": "profit", "reason": "Cost-price data was not provided, so profit cannot be calculated."}
        ],
    )


def test_nvidia_provider_passes_expected_chatnvidia_parameters():
    captured = {}

    class FakeChat:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def with_structured_output(self, schema):
            assert schema is NarrativeDraft
            return RunnableLambda(lambda _input: valid_draft())

    provider = ChatNVIDIANarrativeProvider(
        api_key=SecretStr("secret"),
        model="nvidia/nemotron-3-nano-30b-a3b",
        temperature=0,
        max_tokens=700,
        timeout_seconds=25,
        transport_retries=1,
        base_url="https://integrate.api.nvidia.com/v1",
        chat_model_factory=FakeChat,
    )

    result = asyncio.run(provider.generate_draft(generation_input()))

    assert result.candidate == valid_draft()
    assert captured == {
        "model": "nvidia/nemotron-3-nano-30b-a3b",
        "nvidia_api_key": "secret",
        "temperature": 0,
        "max_completion_tokens": 700,
        "base_url": "https://integrate.api.nvidia.com/v1",
    }


def test_nvidia_provider_uses_ainvoke_and_rejects_missing_key():
    provider = ChatNVIDIANarrativeProvider(
        api_key=None,
        model="model",
        temperature=0,
        max_tokens=700,
        timeout_seconds=25,
        transport_retries=0,
    )
    with pytest.raises(NarrativeProviderNotConfigured):
        asyncio.run(provider.generate_draft(generation_input()))

    class AsyncOnlyChain:
        async def ainvoke(self, payload):
            assert "safe_context" in payload
            return valid_draft()

        def invoke(self, payload):
            raise AssertionError("sync invoke must not be used")

    provider = ChatNVIDIANarrativeProvider(
        api_key=SecretStr("secret"),
        model="model",
        temperature=0,
        max_tokens=700,
        timeout_seconds=25,
        transport_retries=0,
    )
    provider._chain = AsyncOnlyChain()

    result = asyncio.run(provider.generate_draft(generation_input()))
    assert result.candidate == valid_draft()


def test_nvidia_provider_timeout_and_invalid_response_are_classified():
    class SlowChain:
        async def ainvoke(self, payload):
            await asyncio.sleep(0.05)
            return valid_draft()

    provider = ChatNVIDIANarrativeProvider(
        api_key=SecretStr("secret"),
        model="model",
        temperature=0,
        max_tokens=700,
        timeout_seconds=0.001,
        transport_retries=0,
    )
    provider._chain = SlowChain()
    with pytest.raises(NarrativeProviderTimeout):
        asyncio.run(provider.generate_draft(generation_input()))

    class BadChain:
        async def ainvoke(self, payload):
            return {"sections": [], "unavailable_metrics": [], "extra": True}

    provider._chain = BadChain()
    provider.timeout_seconds = 25
    with pytest.raises(NarrativeProviderInvalidResponse):
        asyncio.run(provider.generate_draft(generation_input()))


def test_provider_exception_classification_uses_status_codes():
    class ResponseError(Exception):
        def __init__(self, status_code):
            self.response = type("Response", (), {"status_code": status_code})()

    assert isinstance(classify_provider_exception(ResponseError(401)), NarrativeProviderAuthenticationError)
    assert isinstance(classify_provider_exception(ResponseError(429)), NarrativeProviderRateLimited)
    assert isinstance(classify_provider_exception(ResponseError(503)), NarrativeProviderUnavailable)
    assert isinstance(classify_provider_exception(RuntimeError("network down")), NarrativeProviderUnavailable)


def test_strict_draft_schema_rejects_extra_fields_and_unstructured_output():
    with pytest.raises(ValidationError):
        NarrativeDraft.model_validate(
            {
                "sections": [
                    {
                        "text_template": "Billed {{reconciliation.total_billed_paise}}.",
                        "trace_keys": ["reconciliation.total_billed_paise"],
                        "unexpected": "nope",
                    }
                ],
                "unavailable_metrics": [],
            }
        )

    with pytest.raises(ValidationError):
        NarrativeDraft.model_validate({"text": "Today was good."})


def test_safe_generation_input_excludes_raw_rows_and_visit_ids(client, valid_rows):
    malformed = dict(valid_rows[0])
    malformed["visit_id"] = "RAW-SECRET-VISIT"
    malformed.pop("payment_mode")
    response = client.put(
        "/api/v1/clinic-days/CLN-001/2026-07-27",
        json={"records": [valid_rows[1], malformed]},
    )
    assert response.status_code == 200

    with client.app.state.session_factory() as session:
        from app.models import ClinicDay

        clinic_day = session.query(ClinicDay).filter_by(clinic_id="CLN-001").one()
        catalogue = build_trace_catalogue(clinic_day=clinic_day)
        model_input = build_narrative_generation_input(clinic_day=clinic_day, catalogue=catalogue)
        safe_context, approved_placeholders = serialize_generation_input(model_input)

    payload = safe_context + approved_placeholders
    assert "RAW-SECRET-VISIT" not in payload
    assert "raw_row_json" not in payload
    assert "NVIDIA_API_KEY" not in payload
    assert json.loads(approved_placeholders)["reconciliation.total_billed_paise"] == "₹60"

import os

import pytest
from pydantic import SecretStr

from app.agent.nvidia_client import ChatNVIDIANarrativeProvider
from app.agent.schemas import NarrativeGenerationInput


@pytest.mark.live_nvidia
@pytest.mark.asyncio
async def test_live_nvidia_structured_output_smoke():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key or os.getenv("RUN_LIVE_NVIDIA_TESTS") != "1":
        pytest.skip("Set NVIDIA_API_KEY and RUN_LIVE_NVIDIA_TESTS=1 to run live NVIDIA smoke test.")

    provider = ChatNVIDIANarrativeProvider(
        api_key=SecretStr(api_key),
        model=os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-nano-30b-a3b"),
        temperature=0,
        max_tokens=350,
        timeout_seconds=25,
        transport_retries=0,
        base_url=os.getenv("NVIDIA_BASE_URL") or None,
    )
    result = await provider.generate_draft(
        NarrativeGenerationInput(
            clinic_id="LIVE-CLINIC",
            clinic_name="Live Clinic",
            clinic_location=None,
            business_date="2026-07-27",
            report_hash="sha256:" + "1" * 64,
            accepted_rows=1,
            rejected_rows=0,
            report={
                "metadata": {"business_date": "2026-07-27"},
                "ingestion": {"accepted_rows": 1, "rejected_rows": 0},
                "reconciliation": {
                    "total_billed_paise": 1000,
                    "total_collected_paise": 1000,
                    "total_outstanding_paise": 0,
                    "total_refunds_paise": 0,
                    "collection_rate": 1.0,
                    "pending_visit_count": 0,
                },
                "analytics": {"peak_hour": None, "top_medicines_by_quantity": [], "top_medicines_by_revenue": []},
            },
            approved_placeholders={
                "metadata.business_date": "27 Jul 2026",
                "ingestion.accepted_rows": "1",
                "reconciliation.total_billed_paise": "₹10",
                "reconciliation.total_collected_paise": "₹10",
                "reconciliation.collection_rate": "100%",
            },
        )
    )

    assert result.provider == "nvidia"
    assert result.candidate.sections

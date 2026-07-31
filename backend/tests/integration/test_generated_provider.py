from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.schemas.narrative import NarrativeCandidate, NarrativeSectionCandidate


@dataclass
class GoodProvider:
    name: str = "test_provider"
    model: str = "test-model"

    def generate(self, *, prompt: str, repair_context: str | None = None):
        return NarrativeCandidate(
            sections=[
                NarrativeSectionCandidate(
                    text_template=(
                        "Billed {{reconciliation.total_billed_paise}} across {{ingestion.accepted_rows}} visits; "
                        "collected {{reconciliation.total_collected_paise}} ({{reconciliation.collection_rate}}). "
                        "Outstanding: {{reconciliation.total_outstanding_paise}} across "
                        "{{reconciliation.pending_visit_count}} visits."
                    ),
                    trace_keys=[
                        "reconciliation.total_billed_paise", "ingestion.accepted_rows",
                        "reconciliation.total_collected_paise", "reconciliation.collection_rate",
                        "reconciliation.total_outstanding_paise", "reconciliation.pending_visit_count",
                    ],
                ),
                NarrativeSectionCandidate(
                    text_template=(
                        "Peak: {{analytics.peak_hour.label}} with {{analytics.peak_hour.revenue_paise}}. "
                        "Quantity leader: {{analytics.top_medicines_by_quantity.0.drug_name}} "
                        "({{analytics.top_medicines_by_quantity.0.quantity}} units). "
                        "Revenue leader: {{analytics.top_medicines_by_revenue.0.drug_name}} "
                        "({{analytics.top_medicines_by_revenue.0.revenue_paise}})."
                    ),
                    trace_keys=[
                        "analytics.peak_hour.label", "analytics.peak_hour.revenue_paise",
                        "analytics.top_medicines_by_quantity.0.drug_name",
                        "analytics.top_medicines_by_quantity.0.quantity",
                        "analytics.top_medicines_by_revenue.0.drug_name",
                        "analytics.top_medicines_by_revenue.0.revenue_paise",
                    ],
                ),
            ],
            unavailable_metrics=[],
        )


def test_valid_provider_output_is_marked_generated(valid_rows):
    app = create_app(
        settings=Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"]),
        narrative_provider=GoodProvider(),
    )
    with TestClient(app) as client:
        client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        response = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})
        assert response.status_code == 200
        assert response.json()["status"] == "generated"
        assert response.json()["provider"] == "test_provider"
        assert "Billed ₹105" in response.json()["summary"]
        assert response.json()["unavailable_metrics"][0]["metric"] == "profit"

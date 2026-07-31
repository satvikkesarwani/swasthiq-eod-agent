from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.agent.exceptions import NarrativeProviderAuthenticationError, NarrativeProviderRateLimited, NarrativeProviderTimeout, NarrativeProviderUnavailable
from app.agent.schemas import NarrativeDraft, NarrativeProviderResult
from app.core.config import Settings
from app.main import create_app


@dataclass
class GoodProvider:
    name: str = "test_provider"
    model: str = "test-model"
    calls: int = 0

    async def generate_draft(self, request):
        self.calls += 1
        return NarrativeProviderResult(
            provider=self.name,
            model=self.model,
            generation_ms=7,
            candidate=NarrativeDraft(
                sections=[
                    {
                        "intent": "overview",
                        "text_template": (
                            "Billed {{reconciliation.total_billed_paise}} across {{ingestion.accepted_rows}} visits; "
                            "collected {{reconciliation.total_collected_paise}} ({{reconciliation.collection_rate}}). "
                            "Outstanding: {{reconciliation.total_outstanding_paise}} across "
                            "{{reconciliation.pending_visit_count}} visits."
                        ),
                        "trace_keys": [
                            "reconciliation.total_billed_paise", "ingestion.accepted_rows",
                            "reconciliation.total_collected_paise", "reconciliation.collection_rate",
                            "reconciliation.total_outstanding_paise", "reconciliation.pending_visit_count",
                        ],
                    },
                    {
                        "intent": "peak_hour",
                        "text_template": (
                            "Peak: {{analytics.peak_hour.label}} with {{analytics.peak_hour.revenue_paise}}."
                        ),
                        "trace_keys": [
                            "analytics.peak_hour.label", "analytics.peak_hour.revenue_paise",
                        ],
                    },
                    {
                        "intent": "top_medicine_quantity",
                        "text_template": (
                            "Quantity leader: {{analytics.top_medicines_by_quantity.0.drug_name}} "
                            "with {{analytics.top_medicines_by_quantity.0.quantity}} units."
                        ),
                        "trace_keys": [
                            "analytics.top_medicines_by_quantity.0.drug_name",
                            "analytics.top_medicines_by_quantity.0.quantity",
                        ],
                    },
                    {
                        "intent": "top_medicine_revenue",
                        "text_template": (
                            "Revenue leader: {{analytics.top_medicines_by_revenue.0.drug_name}} "
                            "with {{analytics.top_medicines_by_revenue.0.revenue_paise}}."
                        ),
                        "trace_keys": [
                            "analytics.top_medicines_by_revenue.0.drug_name",
                            "analytics.top_medicines_by_revenue.0.revenue_paise",
                        ],
                    },
                ],
                unavailable_metrics=[
                    {"metric": "profit", "reason": "Cost prices were not provided in the billing data."}
                ],
            ),
        )


@dataclass
class InvalidGroundingProvider:
    name: str = "test_provider"
    model: str = "test-model"

    async def generate_draft(self, request):
        return NarrativeProviderResult(
            provider=self.name,
            model=self.model,
            generation_ms=5,
            candidate=NarrativeDraft(
                sections=[
                    {
                        "intent": "overview",
                        "text_template": "Only collected {{reconciliation.total_collected_paise}}.",
                        "trace_keys": ["reconciliation.total_collected_paise"],
                    }
                ],
                unavailable_metrics=[
                    {"metric": "profit", "reason": "Cost prices were not provided in the billing data."}
                ],
            ),
        )


@dataclass
class StaleProvider(GoodProvider):
    session_factory = None

    async def generate_draft(self, request):
        with self.session_factory() as session:
            from app.models import ClinicDay

            clinic_day = session.query(ClinicDay).filter_by(clinic_id=request.clinic_id).one()
            clinic_day.report_hash = "sha256:" + "f" * 64
            session.commit()
        return NarrativeProviderResult(
            provider=self.name,
            model=self.model,
            generation_ms=9,
            candidate=NarrativeDraft(
                sections=[
                    {
                        "intent": "overview",
                        "text_template": (
                            "Billed {{reconciliation.total_billed_paise}} across {{ingestion.accepted_rows}} visits; "
                            "collected {{reconciliation.total_collected_paise}} ({{reconciliation.collection_rate}}). "
                            "Outstanding: {{reconciliation.total_outstanding_paise}} across "
                            "{{reconciliation.pending_visit_count}} visits."
                        ),
                        "trace_keys": [
                            "reconciliation.total_billed_paise",
                            "ingestion.accepted_rows",
                            "reconciliation.total_collected_paise",
                            "reconciliation.collection_rate",
                            "reconciliation.total_outstanding_paise",
                            "reconciliation.pending_visit_count",
                        ],
                    },
                    {
                        "intent": "peak_hour",
                        "text_template": (
                            "Peak: {{analytics.peak_hour.label}} with {{analytics.peak_hour.revenue_paise}}."
                        ),
                        "trace_keys": [
                            "analytics.peak_hour.label",
                            "analytics.peak_hour.revenue_paise",
                        ],
                    },
                    {
                        "intent": "top_medicine_quantity",
                        "text_template": (
                            "Quantity leader: {{analytics.top_medicines_by_quantity.0.drug_name}} "
                            "with {{analytics.top_medicines_by_quantity.0.quantity}} units."
                        ),
                        "trace_keys": [
                            "analytics.top_medicines_by_quantity.0.drug_name",
                            "analytics.top_medicines_by_quantity.0.quantity",
                        ],
                    },
                    {
                        "intent": "top_medicine_revenue",
                        "text_template": (
                            "Revenue leader: {{analytics.top_medicines_by_revenue.0.drug_name}} "
                            "with {{analytics.top_medicines_by_revenue.0.revenue_paise}}."
                        ),
                        "trace_keys": [
                            "analytics.top_medicines_by_revenue.0.drug_name",
                            "analytics.top_medicines_by_revenue.0.revenue_paise",
                        ],
                    },
                ],
                unavailable_metrics=[],
            ),
        )


@dataclass
class RepairProvider(GoodProvider):
    repair_is_valid: bool = True
    timeout_on_repair: bool = False
    feedback_seen: list[str] | None = None

    async def generate_draft(self, request, *, repair_feedback=None, invalid_draft=None):
        self.calls += 1
        if repair_feedback:
            self.feedback_seen = repair_feedback
            if self.timeout_on_repair:
                raise NarrativeProviderTimeout()
            if self.repair_is_valid:
                return NarrativeProviderResult(
                    provider=self.name,
                    model=self.model,
                    generation_ms=7,
                    candidate=NarrativeDraft(
                        sections=[
                            {
                                "intent": "overview",
                                "text_template": (
                                    "Billed {{reconciliation.total_billed_paise}} across {{ingestion.accepted_rows}} visits; "
                                    "collected {{reconciliation.total_collected_paise}} ({{reconciliation.collection_rate}}). "
                                    "Outstanding: {{reconciliation.total_outstanding_paise}} across "
                                    "{{reconciliation.pending_visit_count}} visits."
                                ),
                                "trace_keys": [
                                    "reconciliation.total_billed_paise", "ingestion.accepted_rows",
                                    "reconciliation.total_collected_paise", "reconciliation.collection_rate",
                                    "reconciliation.total_outstanding_paise", "reconciliation.pending_visit_count",
                                ],
                            },
                            {
                                "intent": "peak_hour",
                                "text_template": "Peak: {{analytics.peak_hour.label}} with {{analytics.peak_hour.revenue_paise}}.",
                                "trace_keys": ["analytics.peak_hour.label", "analytics.peak_hour.revenue_paise"],
                            },
                            {
                                "intent": "top_medicine_quantity",
                                "text_template": (
                                    "Quantity leader: {{analytics.top_medicines_by_quantity.0.drug_name}} "
                                    "with {{analytics.top_medicines_by_quantity.0.quantity}} units."
                                ),
                                "trace_keys": [
                                    "analytics.top_medicines_by_quantity.0.drug_name",
                                    "analytics.top_medicines_by_quantity.0.quantity",
                                ],
                            },
                            {
                                "intent": "top_medicine_revenue",
                                "text_template": (
                                    "Revenue leader: {{analytics.top_medicines_by_revenue.0.drug_name}} "
                                    "with {{analytics.top_medicines_by_revenue.0.revenue_paise}}."
                                ),
                                "trace_keys": [
                                    "analytics.top_medicines_by_revenue.0.drug_name",
                                    "analytics.top_medicines_by_revenue.0.revenue_paise",
                                ],
                            },
                        ],
                        unavailable_metrics=[
                            {"metric": "profit", "reason": "Cost prices were not provided in the billing data."}
                        ],
                    ),
                )
        return NarrativeProviderResult(
            provider=self.name,
            model=self.model,
            generation_ms=3,
            candidate=NarrativeDraft(
                sections=[
                    {
                        "intent": "overview",
                        "text_template": "Only collected {{reconciliation.total_collected_paise}}.",
                        "trace_keys": ["reconciliation.total_collected_paise"],
                    }
                ],
                unavailable_metrics=[{"metric": "profit", "reason": "Cost prices were not provided in the billing data."}],
            ),
        )


@dataclass
class ErrorProvider:
    error: Exception
    name: str = "test_provider"
    model: str = "test-model"
    calls: int = 0

    async def generate_draft(self, request, **kwargs):
        self.calls += 1
        raise self.error


def test_valid_provider_output_is_marked_generated(valid_rows):
    provider = GoodProvider()
    app = create_app(
        settings=Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"]),
        narrative_provider=provider,
    )
    with TestClient(app) as client:
        client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        response = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})
        assert response.status_code == 200
        assert response.json()["status"] == "generated"
        assert response.json()["provider"] == "test_provider"
        assert response.json()["generation_ms"] == 7
        assert "Billed ₹105" in response.json()["summary"]
        assert response.json()["unavailable_metrics"][0]["metric"] == "profit"

        cached = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})
        forced = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": True})
        assert cached.json()["generation_ms"] == 7
        assert forced.json()["status"] == "generated"
        assert provider.calls == 2


def test_invalid_provider_grounding_falls_back_without_saving_raw_output(valid_rows):
    app = create_app(
        settings=Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"]),
        narrative_provider=InvalidGroundingProvider(),
    )
    with TestClient(app) as client:
        client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        response = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})
        body = response.json()

        assert response.status_code == 200
        assert body["status"] == "fallback"
        assert body["fallback_reason_code"] == "GROUNDING_VALIDATION_FAILED"
        assert "Only collected" not in body["summary"]

        fetched = client.get("/api/v1/clinic-days/CLN-001/2026-07-27/narrative")
        assert fetched.json()["summary"] == body["summary"]
        assert "Only collected" not in fetched.json()["summary"]


def test_semantic_repair_success_uses_exactly_two_calls(valid_rows):
    provider = RepairProvider(repair_is_valid=True)
    app = create_app(
        settings=Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"]),
        narrative_provider=provider,
    )
    with TestClient(app) as client:
        client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        response = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})

        assert response.json()["status"] == "generated"
        assert provider.calls == 2
        assert provider.feedback_seen
        assert "Only collected" not in response.json()["summary"]


def test_semantic_repair_failure_falls_back_and_does_not_third_call(valid_rows):
    provider = RepairProvider(repair_is_valid=False)
    app = create_app(
        settings=Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"]),
        narrative_provider=provider,
    )
    with TestClient(app) as client:
        client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        response = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})

        assert response.json()["status"] == "fallback"
        assert response.json()["fallback_reason_code"] == "REPAIR_FAILED"
        assert provider.calls == 2


def test_provider_transport_errors_do_not_trigger_semantic_repair(valid_rows):
    for error, reason in [
        (NarrativeProviderTimeout(), "PROVIDER_TIMEOUT"),
        (NarrativeProviderAuthenticationError(), "PROVIDER_AUTHENTICATION_FAILED"),
        (NarrativeProviderRateLimited(), "PROVIDER_RATE_LIMITED"),
        (NarrativeProviderUnavailable(), "PROVIDER_UNAVAILABLE"),
    ]:
        provider = ErrorProvider(error=error)
        app = create_app(
            settings=Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"]),
            narrative_provider=provider,
        )
        with TestClient(app) as client:
            client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
            response = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})
            assert response.json()["status"] == "fallback"
            assert response.json()["fallback_reason_code"] == reason
            assert provider.calls == 1


def test_generation_for_outdated_report_hash_is_not_saved(valid_rows):
    provider = StaleProvider()
    app = create_app(
        settings=Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"]),
        narrative_provider=provider,
    )
    provider.session_factory = app.state.session_factory

    with TestClient(app, raise_server_exceptions=False) as client:
        client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        response = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "NARRATIVE_REPORT_CHANGED"
        assert client.get("/api/v1/clinic-days/CLN-001/2026-07-27/narrative").status_code == 404

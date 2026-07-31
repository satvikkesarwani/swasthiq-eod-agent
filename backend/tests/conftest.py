from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.integrations.llm_provider import DisabledNarrativeProvider
from app.main import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    settings = Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"])
    app = create_app(settings=settings, narrative_provider=DisabledNarrativeProvider())
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client


@pytest.fixture
def valid_rows() -> list[dict]:
    return [
        {
            "clinic_id": "CLN-001",
            "visit_id": "V-001",
            "timestamp": "2026-07-27T09:00:00Z",
            "doctor_id": "DOC-1",
            "line_items": [{"drug_name": "PARACETAMOL", "qty": 2, "unit_price_paise": 2500}],
            "payment_mode": "cash",
            "amount_paid_paise": 4000,
            "discount_paise": 500,
            "is_refund": False,
        },
        {
            "clinic_id": "CLN-001",
            "visit_id": "V-002",
            "timestamp": "2026-07-27T10:00:00Z",
            "doctor_id": "DOC-2",
            "line_items": [{"drug_name": "AMOXICILLIN", "qty": 1, "unit_price_paise": 6000}],
            "payment_mode": "upi",
            "amount_paid_paise": 6000,
            "discount_paise": 0,
            "is_refund": False,
        },
    ]

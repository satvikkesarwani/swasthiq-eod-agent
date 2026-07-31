import asyncio
import json
from datetime import date

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.integrations.llm_provider import DisabledNarrativeProvider
from app.main import create_app
from app.models import ClinicDay, IngestionError


def _fresh_client(**settings_overrides):
    settings = Settings(
        app_env="test",
        database_url="sqlite://",
        cors_origins=["http://test"],
        **settings_overrides,
    )
    app = create_app(settings=settings, narrative_provider=DisabledNarrativeProvider())
    return TestClient(app, raise_server_exceptions=True)


def _stored_clinic_day(client, clinic_id="CLN-001", business_date="2026-07-27"):
    parsed_date = date.fromisoformat(business_date)
    with client.app.state.session_factory() as session:
        return session.query(ClinicDay).filter_by(clinic_id=clinic_id, business_date=parsed_date).one()


async def _asgi_request_without_content_length(app, *, path: str, body: bytes):
    messages = []
    chunks = [body[: len(body) // 2], body[len(body) // 2 :]]

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "PUT",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [(b"content-type", b"application/json"), (b"x-request-id", b"req-stream")],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    async def receive():
        if chunks:
            chunk = chunks.pop(0)
            return {"type": "http.request", "body": chunk, "more_body": bool(chunks)}
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    status = next(message["status"] for message in messages if message["type"] == "http.response.start")
    response_body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
    return status, json.loads(response_body.decode())


def test_create_read_and_list_clinic_day(client, valid_rows):
    response = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["report"]["reconciliation"]["total_billed_paise"] == 10500

    get_response = client.get("/api/v1/clinic-days/CLN-001/2026-07-27")
    assert get_response.status_code == 200
    assert get_response.json()["report_hash"].startswith("sha256:")

    list_response = client.get("/api/v1/clinic-days", params={"clinic_id": "CLN-001"})
    assert len(list_response.json()["items"]) == 1


def test_partial_ingestion_uses_only_valid_rows(client, valid_rows):
    malformed = dict(valid_rows[0])
    malformed["visit_id"] = "BAD"
    malformed.pop("payment_mode")
    response = client.put(
        "/api/v1/clinic-days/CLN-001/2026-07-27",
        json={"records": [valid_rows[0], malformed]},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed_with_errors"
    assert body["ingestion"]["accepted_rows"] == 1
    assert body["ingestion"]["rejected_rows"] == 1
    assert body["ingestion"]["errors"][0]["field"] == "payment_mode"


def test_all_invalid_rows_do_not_create_report(client, valid_rows):
    malformed = dict(valid_rows[0])
    malformed.pop("payment_mode")
    response = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": [malformed]})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NO_VALID_ROWS"
    assert client.get("/api/v1/clinic-days/CLN-001/2026-07-27").status_code == 404


def test_empty_day_is_valid(client):
    response = client.put("/api/v1/clinic-days/CLN-001/2026-07-26", json={"records": []})
    assert response.status_code == 201
    assert response.json()["report"]["analytics"]["peak_hour"] is None


def test_fallback_narrative_is_grounded_and_reused(client, valid_rows):
    client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
    first = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})
    assert first.status_code == 200
    body = first.json()
    assert body["status"] == "fallback"
    assert "₹105" in body["summary"]
    assert all(trace["report_path"] for trace in body["traces"])

    second = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})
    assert second.json() == body


def test_reimport_invalidates_old_narrative(client, valid_rows):
    client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
    client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})

    changed = [dict(valid_rows[0])]
    changed[0]["amount_paid_paise"] = 4500
    replace = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": changed})
    assert replace.status_code == 200
    assert replace.json()["narrative_status"] == "not_generated"
    assert client.get("/api/v1/clinic-days/CLN-001/2026-07-27/narrative").status_code == 404


def test_replacement_counts_unique_rejected_rows_and_preserves_all_invalid_report(client, valid_rows):
    create_response = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
    original_hash = create_response.json()["report_hash"]

    malformed = dict(valid_rows[0])
    malformed["visit_id"] = "BAD-MULTI"
    malformed.pop("payment_mode")
    malformed["doctor_id"] = ""
    malformed["line_items"] = [{"drug_name": "", "qty": 0, "unit_price_paise": -1}]
    replacement = client.put(
        "/api/v1/clinic-days/CLN-001/2026-07-27",
        json={"records": [valid_rows[1], malformed]},
    )

    assert replacement.status_code == 200
    body = replacement.json()
    assert body["ingestion"]["accepted_rows"] == 1
    assert body["ingestion"]["rejected_rows"] == 1
    assert len(body["ingestion"]["errors"]) > 1
    stored = _stored_clinic_day(client)
    assert stored.accepted_rows == body["ingestion"]["accepted_rows"]
    assert stored.rejected_rows == body["ingestion"]["rejected_rows"]

    all_invalid = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": [malformed]})
    assert all_invalid.status_code == 422
    assert client.get("/api/v1/clinic-days/CLN-001/2026-07-27").json()["report_hash"] != original_hash
    assert client.get("/api/v1/clinic-days/CLN-001/2026-07-27").json()["ingestion"]["accepted_rows"] == 1


def test_zero_priced_line_item_is_accepted_and_counted(client, valid_rows):
    zero_price = {
        "clinic_id": "CLN-001",
        "visit_id": "FREE-1",
        "timestamp": "2026-07-27T11:00:00Z",
        "doctor_id": "DOC-3",
        "line_items": [{"drug_name": "Sample Strip", "qty": 4, "unit_price_paise": 0}],
        "payment_mode": "card",
        "amount_paid_paise": 0,
        "discount_paise": 0,
        "is_refund": False,
    }

    response = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows + [zero_price]})
    assert response.status_code == 201
    body = response.json()
    assert body["ingestion"]["accepted_rows"] == 3
    assert body["report"]["reconciliation"]["total_billed_paise"] == 10_500
    quantity_leader = body["report"]["analytics"]["top_medicines_by_quantity"][0]
    assert quantity_leader == {"rank": 1, "drug_name": "SAMPLE STRIP", "quantity": 4}
    revenue_row = next(
        row for row in body["report"]["analytics"]["top_medicines_by_revenue"] if row["drug_name"] == "SAMPLE STRIP"
    )
    assert revenue_row["revenue_paise"] == 0

    negative = dict(zero_price)
    negative["visit_id"] = "NEG-PRICE"
    negative["line_items"] = [{"drug_name": "Bad", "qty": 1, "unit_price_paise": -1}]
    rejected = client.put("/api/v1/clinic-days/CLN-002/2026-07-27", json={"records": [negative]})
    assert rejected.status_code == 422
    assert rejected.json()["error"]["details"][0]["field"] == "line_items.0.unit_price_paise"


def test_raw_rejected_rows_are_not_persisted_or_returned_by_default(valid_rows):
    with _fresh_client() as local_client:
        malformed = dict(valid_rows[0])
        malformed.pop("payment_mode")
        response = local_client.put(
            "/api/v1/clinic-days/CLN-001/2026-07-27",
            json={"records": [valid_rows[1], malformed]},
        )
        assert response.status_code == 201
        assert "raw_row_json" not in response.text
        with local_client.app.state.session_factory() as session:
            stored_error = session.query(IngestionError).one()
            assert stored_error.raw_row_json is None


def test_raw_rejected_rows_can_be_persisted_when_explicitly_enabled(valid_rows):
    with _fresh_client(store_rejected_raw_rows=True) as local_client:
        malformed = dict(valid_rows[0])
        malformed.pop("payment_mode")
        response = local_client.put(
            "/api/v1/clinic-days/CLN-001/2026-07-27",
            json={"records": [valid_rows[1], malformed]},
        )
        assert response.status_code == 201
        assert "raw_row_json" not in response.text
        with local_client.app.state.session_factory() as session:
            stored_error = session.query(IngestionError).one()
            assert stored_error.raw_row_json["visit_id"] == "V-001"


def test_oversized_body_with_content_length_is_rejected_and_does_not_replace(valid_rows):
    with _fresh_client() as local_client:
        created = local_client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        original_hash = created.json()["report_hash"]
        local_client.app.state.settings.max_request_body_bytes = 160

        response = local_client.put(
            "/api/v1/clinic-days/CLN-001/2026-07-27",
            content=json.dumps({"records": valid_rows * 20}),
            headers={"Content-Type": "application/json", "X-Request-ID": "req-too-large"},
        )
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"
        assert response.json()["error"]["request_id"] == "req-too-large"
        assert local_client.get("/api/v1/clinic-days/CLN-001/2026-07-27").json()["report_hash"] == original_hash


def test_streamed_oversized_body_without_content_length_is_rejected(valid_rows):
    with _fresh_client(max_request_body_bytes=200) as local_client:
        body = json.dumps({"records": valid_rows * 20}).encode()
        status, payload = asyncio.run(
            _asgi_request_without_content_length(
                local_client.app,
                path="/api/v1/clinic-days/CLN-001/2026-07-27",
                body=body,
            )
        )
        assert status == 413
        assert payload["error"]["code"] == "REQUEST_TOO_LARGE"
        assert payload["error"]["request_id"] == "req-stream"
        assert local_client.get("/api/v1/clinic-days/CLN-001/2026-07-27").status_code == 404


def test_request_at_or_under_body_limit_succeeds(valid_rows):
    body = json.dumps({"records": [valid_rows[0]]}).encode()
    with _fresh_client(max_request_body_bytes=len(body)) as local_client:
        response = local_client.put(
            "/api/v1/clinic-days/CLN-001/2026-07-27",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201
        assert response.json()["ingestion"]["accepted_rows"] == 1

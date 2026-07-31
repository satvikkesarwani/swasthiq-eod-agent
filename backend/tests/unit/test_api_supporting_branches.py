import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError, SecretStr

from app.agent.exceptions import NarrativeProviderDisabled
from app.core.config import Settings
from app.core.errors import AppError
from app.core.money import format_paise, format_rate
from app.integrations.llm_provider import ChatNVIDIANarrativeProvider, DisabledNarrativeProvider
from app.main import create_app


def test_settings_parse_cors_origins_from_comma_string():
    settings = Settings(cors_origins="http://one.test, http://two.test,,")
    assert settings.cors_origins == ["http://one.test", "http://two.test"]


def test_app_builds_nvidia_provider_when_configured():
    app = create_app(
        settings=Settings(
            app_env="test",
            database_url="sqlite://",
            cors_origins=["http://test"],
            llm_provider="nvidia",
            nvidia_api_key="test-key",
            nvidia_model="test-model",
            nvidia_base_url="https://integrate.api.nvidia.com/v1",
        )
    )
    assert app.state.narrative_provider.name == "nvidia"
    assert app.state.narrative_provider.model == "test-model"
    assert app.state.narrative_provider.base_url == "https://integrate.api.nvidia.com/v1"
    app.state.engine.dispose()


def test_disabled_provider_and_app_error_string_are_safe():
    provider = DisabledNarrativeProvider()
    with pytest.raises(NarrativeProviderDisabled):
        asyncio.run(provider.generate_draft(None))

    error = AppError(code="X", message="Safe message")
    assert str(error) == "Safe message"


def test_llm_settings_are_bounded_and_secret_is_masked():
    settings = Settings(nvidia_api_key="secret-value")
    assert isinstance(settings.nvidia_api_key, SecretStr)
    assert settings.nvidia_api_key.get_secret_value() == "secret-value"
    assert "secret-value" not in repr(settings)

    with pytest.raises(ValidationError):
        Settings(llm_temperature=1.5)
    with pytest.raises(ValidationError):
        Settings(llm_max_tokens=0)
    with pytest.raises(ValidationError):
        Settings(llm_timeout_seconds=0)


def test_chat_nvidia_provider_does_not_initialize_model_until_generation():
    calls = []

    def factory(**kwargs):
        calls.append(kwargs)
        raise AssertionError("factory should not be called during construction")

    provider = ChatNVIDIANarrativeProvider(
        api_key=SecretStr("secret"),
        model="model",
        temperature=0,
        max_tokens=700,
        timeout_seconds=25,
        transport_retries=1,
        chat_model_factory=factory,
    )
    assert provider.name == "nvidia"
    assert calls == []


def test_health_and_not_found_error_paths(client):
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["database"] == "connected"

    errors = client.get("/api/v1/clinic-days/CLN-404/2026-07-27/errors")
    assert errors.status_code == 404
    assert errors.json()["error"]["code"] == "CLINIC_DAY_NOT_FOUND"


def test_health_database_failure_returns_safe_error():
    app = create_app(
        settings=Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"]),
        narrative_provider=DisabledNarrativeProvider(),
    )

    class BrokenSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, statement):
            raise RuntimeError("sqlite:////private/clinic.db should not leak")

    app.state.session_factory = lambda: BrokenSession()
    with TestClient(app, raise_server_exceptions=False) as local_client:
        response = local_client.get("/api/v1/health", headers={"X-Request-ID": "req-health"})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.json()["error"]["request_id"] == "req-health"
    assert "private/clinic" not in response.text


def test_unexpected_errors_return_safe_envelope():
    app = create_app(
        settings=Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"]),
        narrative_provider=DisabledNarrativeProvider(),
    )

    @app.get("/boom")
    def boom():
        raise RuntimeError("database internals should not leak")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom", headers={"X-Request-ID": "req-boom"})

    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "INTERNAL_ERROR",
        "message": "An unexpected error occurred.",
        "details": [],
        "request_id": "req-boom",
    }
    assert "database internals" not in response.text


def test_invalid_content_length_falls_back_to_actual_body_check(valid_rows):
    app = create_app(
        settings=Settings(app_env="test", database_url="sqlite://", cors_origins=["http://test"]),
        narrative_provider=DisabledNarrativeProvider(),
    )
    body = json.dumps({"records": [valid_rows[0]]}).encode()
    messages = []

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "PUT",
        "scheme": "http",
        "path": "/api/v1/clinic-days/CLN-001/2026-07-27",
        "raw_path": b"/api/v1/clinic-days/CLN-001/2026-07-27",
        "query_string": b"",
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", b"not-an-integer"),
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    asyncio.run(app(scope, receive, send))
    assert next(message["status"] for message in messages if message["type"] == "http.response.start") == 200
    app.state.engine.dispose()


def test_money_formatting_decimal_and_rate_branches():
    assert format_paise(10_550) == "₹105.50"
    assert format_rate(0.955) == "95.5%"

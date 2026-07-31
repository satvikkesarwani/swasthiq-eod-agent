import asyncio
import time
from dataclasses import dataclass
from typing import Any

from pydantic import SecretStr, ValidationError

from app.agent.context import serialize_generation_input
from app.agent.exceptions import (
    NarrativeProviderAuthenticationError,
    NarrativeProviderDisabled,
    NarrativeProviderError,
    NarrativeProviderInvalidResponse,
    NarrativeProviderNotConfigured,
    NarrativeProviderRateLimited,
    NarrativeProviderTimeout,
    NarrativeProviderUnavailable,
)
from app.agent.prompts import build_prompt
from app.agent.schemas import NarrativeDraft, NarrativeGenerationInput, NarrativeProviderResult


@dataclass(slots=True)
class DisabledNarrativeProvider:
    name: str = "disabled"
    model: str | None = None

    async def generate_draft(self, request: NarrativeGenerationInput) -> NarrativeProviderResult:
        raise NarrativeProviderDisabled()


class ChatNVIDIANarrativeProvider:
    name = "nvidia"

    def __init__(
        self,
        *,
        api_key: SecretStr | None,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: float,
        transport_retries: int,
        base_url: str | None = None,
        chat_model_factory: Any | None = None,
    ):
        self._api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.transport_retries = transport_retries
        self.base_url = base_url
        self._chat_model_factory = chat_model_factory
        self._chain = None

    def _build_chain(self):
        if self._api_key is None or not self._api_key.get_secret_value():
            raise NarrativeProviderNotConfigured()
        if self._chain is None:
            if self._chat_model_factory is None:
                from langchain_nvidia_ai_endpoints import ChatNVIDIA

                self._chat_model_factory = ChatNVIDIA

            kwargs: dict[str, Any] = {
                "model": self.model,
                "nvidia_api_key": self._api_key.get_secret_value(),
                "temperature": self.temperature,
                "max_completion_tokens": self.max_tokens,
            }
            if self.base_url:
                kwargs["base_url"] = self.base_url

            model = self._chat_model_factory(**kwargs).with_structured_output(NarrativeDraft)
            self._chain = build_prompt() | model
        return self._chain

    async def generate_draft(self, request: NarrativeGenerationInput) -> NarrativeProviderResult:
        chain = self._build_chain()
        safe_context, approved_placeholders = serialize_generation_input(request)
        attempts = self.transport_retries + 1
        last_error: NarrativeProviderError | None = None
        started = time.perf_counter()

        for attempt in range(attempts):
            try:
                async with asyncio.timeout(self.timeout_seconds):
                    result = await chain.ainvoke(
                        {
                            "safe_context": safe_context,
                            "approved_placeholders": approved_placeholders,
                        }
                    )
                candidate = result if isinstance(result, NarrativeDraft) else NarrativeDraft.model_validate(result)
                generation_ms = int((time.perf_counter() - started) * 1000)
                return NarrativeProviderResult(
                    candidate=candidate,
                    provider=self.name,
                    model=self.model,
                    generation_ms=generation_ms,
                )
            except TimeoutError as exc:
                last_error = NarrativeProviderTimeout()
                if attempt + 1 >= attempts:
                    raise last_error from exc
            except ValidationError as exc:
                raise NarrativeProviderInvalidResponse() from exc
            except Exception as exc:
                classified = classify_provider_exception(exc)
                if isinstance(classified, (NarrativeProviderAuthenticationError, NarrativeProviderRateLimited, NarrativeProviderInvalidResponse)):
                    raise classified from exc
                last_error = classified
                if attempt + 1 >= attempts:
                    raise classified from exc

        raise last_error or NarrativeProviderUnavailable()


def classify_provider_exception(exc: Exception) -> NarrativeProviderError:
    status_code = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if status_code is None and response is not None:
        status_code = getattr(response, "status_code", None)
    message = f"{type(exc).__name__} {status_code or ''}".lower()

    if status_code in {401, 403} or "unauthorized" in message or "authentication" in message:
        return NarrativeProviderAuthenticationError()
    if status_code == 429 or "rate limit" in message or "ratelimit" in message:
        return NarrativeProviderRateLimited()
    if status_code is not None and 500 <= int(status_code) <= 599:
        return NarrativeProviderUnavailable()
    return NarrativeProviderUnavailable()


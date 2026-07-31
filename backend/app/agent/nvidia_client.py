import asyncio
import threading
import time
from dataclasses import dataclass
from typing import Any, Sequence

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

    async def generate_draft(
        self,
        request: NarrativeGenerationInput,
        *,
        repair_feedback: list[str] | None = None,
        invalid_draft: dict | None = None,
    ) -> NarrativeProviderResult:
        raise NarrativeProviderDisabled()


class ChatNVIDIANarrativeProvider:
    name = "nvidia"

    def __init__(
        self,
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: float,
        transport_retries: int,
        api_key: SecretStr | None = None,
        api_keys: Sequence[SecretStr] | None = None,
        base_url: str | None = None,
        chat_model_factory: Any | None = None,
    ):
        keys = list(api_keys or [])
        if not keys and api_key is not None:
            keys = [api_key]
        self._api_keys = [key for key in keys if key.get_secret_value()]
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.transport_retries = transport_retries
        self.base_url = base_url
        self._chat_model_factory = chat_model_factory
        self._chains: dict[int, Any] = {}
        self._next_key_index = 0
        self._rotation_lock = threading.Lock()

    @property
    def key_count(self) -> int:
        return len(self._api_keys)

    def _select_key_index(self) -> int:
        if not self._api_keys:
            raise NarrativeProviderNotConfigured()
        with self._rotation_lock:
            key_index = self._next_key_index
            self._next_key_index = (self._next_key_index + 1) % len(self._api_keys)
        return key_index

    def _build_chain(self, key_index: int):
        injected_chain = getattr(self, "_chain", None)
        if injected_chain is not None:
            return injected_chain
        if key_index not in self._chains:
            if self._chat_model_factory is None:
                from langchain_nvidia_ai_endpoints import ChatNVIDIA

                self._chat_model_factory = ChatNVIDIA

            api_key = self._api_keys[key_index]
            kwargs: dict[str, Any] = {
                "model": self.model,
                "nvidia_api_key": api_key.get_secret_value(),
                "temperature": self.temperature,
                "max_completion_tokens": self.max_tokens,
            }
            if self.base_url:
                kwargs["base_url"] = self.base_url

            model = self._chat_model_factory(**kwargs).with_structured_output(NarrativeDraft)
            self._chains[key_index] = build_prompt() | model
        return self._chains[key_index]

    async def generate_draft(
        self,
        request: NarrativeGenerationInput,
        *,
        repair_feedback: list[str] | None = None,
        invalid_draft: dict | None = None,
    ) -> NarrativeProviderResult:
        key_index = self._select_key_index()
        chain = self._build_chain(key_index)
        if repair_feedback:
            request = request.model_copy(update={
                "repair_feedback": repair_feedback[:12],
                "invalid_draft": invalid_draft,
            })
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
                            "repair_feedback": json_safe(repair_feedback or []),
                            "invalid_draft": json_safe(invalid_draft or {}),
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


def json_safe(value: Any) -> str:
    import json

    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return rendered[:4_000]

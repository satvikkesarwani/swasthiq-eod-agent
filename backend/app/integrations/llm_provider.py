import json
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.schemas.narrative import NarrativeCandidate


class NarrativeProvider(Protocol):
    name: str
    model: str | None

    def generate(self, *, prompt: str, repair_context: str | None = None) -> NarrativeCandidate:
        ...


@dataclass(slots=True)
class DisabledNarrativeProvider:
    name: str = "disabled"
    model: str | None = None

    def generate(self, *, prompt: str, repair_context: str | None = None) -> NarrativeCandidate:
        raise RuntimeError("No LLM provider is configured.")


@dataclass(slots=True)
class OpenAICompatibleNarrativeProvider:
    api_key: str
    base_url: str
    model: str
    timeout_seconds: float = 20.0
    name: str = "openai_compatible"

    def generate(self, *, prompt: str, repair_context: str | None = None) -> NarrativeCandidate:
        final_prompt = prompt
        if repair_context:
            final_prompt += "\n\nThe previous response failed validation. Correct it using this error only: " + repair_context

        schema = NarrativeCandidate.model_json_schema()
        payload = {
            "model": self.model,
            "temperature": 0,
            "store": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You write concise clinic-owner end-of-day summaries. "
                        "Never calculate, infer, or invent a number. Use only the exact {{trace.key}} "
                        "placeholders supplied by the user. Do not type literal digits anywhere in text_template."
                    ),
                },
                {"role": "user", "content": final_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "clinic_eod_narrative",
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        response = httpx.post(
            f"{self.base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        if isinstance(content, str):
            content = json.loads(content)
        return NarrativeCandidate.model_validate(content)

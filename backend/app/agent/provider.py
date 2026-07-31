from typing import Protocol

from app.agent.schemas import NarrativeGenerationInput, NarrativeProviderResult


class NarrativeModelProvider(Protocol):
    name: str
    model: str | None

    async def generate_draft(
        self,
        request: NarrativeGenerationInput,
        *,
        repair_feedback: list[str] | None = None,
        invalid_draft: dict | None = None,
    ) -> NarrativeProviderResult:
        ...

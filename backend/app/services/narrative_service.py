from typing import Any

from sqlalchemy.orm import Session

from app.agent.classifier import classify_day
from app.agent.context import build_narrative_generation_input
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
from app.agent.fallback import build_fallback_draft
from app.agent.facts import build_fact_catalogue
from app.agent.validation import GroundingValidationError, RenderedNarrative, validate_draft
from app.core.errors import AppError
from app.integrations.llm_provider import NarrativeProvider
from app.repositories.clinic_day_repository import ClinicDayRepository
from app.repositories.narrative_repository import NarrativeRepository
from app.schemas.narrative import NarrativeResponse


class NarrativeService:
    def __init__(self, session: Session, provider: NarrativeProvider):
        self.session = session
        self.provider = provider
        self.clinic_days = ClinicDayRepository(session)
        self.narratives = NarrativeRepository(session)

    @staticmethod
    def _fallback_reason(exc: NarrativeProviderError | GroundingValidationError | None, *, repair_failed: bool = False) -> str:
        if repair_failed:
            return "REPAIR_FAILED"
        if isinstance(exc, NarrativeProviderDisabled):
            return "LLM_DISABLED"
        if isinstance(exc, NarrativeProviderNotConfigured):
            return "PROVIDER_NOT_CONFIGURED"
        if isinstance(exc, NarrativeProviderAuthenticationError):
            return "PROVIDER_AUTHENTICATION_FAILED"
        if isinstance(exc, NarrativeProviderRateLimited):
            return "PROVIDER_RATE_LIMITED"
        if isinstance(exc, NarrativeProviderTimeout):
            return "PROVIDER_TIMEOUT"
        if isinstance(exc, NarrativeProviderUnavailable):
            return "PROVIDER_UNAVAILABLE"
        if isinstance(exc, NarrativeProviderInvalidResponse):
            return "PROVIDER_INVALID_RESPONSE"
        return "GROUNDING_VALIDATION_FAILED"

    @staticmethod
    def _fallback_rendered(*, clinic_day: Any, catalogue, day_type, flags) -> RenderedNarrative:
        fallback = build_fallback_draft(day_type=day_type, flags=flags, catalogue=catalogue)
        return validate_draft(draft=fallback, catalogue=catalogue, day_type=day_type, flags=flags)

    async def generate(self, *, clinic_id: str, business_date, force_regenerate: bool = False) -> NarrativeResponse:
        clinic_day = self.clinic_days.get(clinic_id, business_date, with_children=True)
        if clinic_day is None:
            raise AppError(code="CLINIC_DAY_NOT_FOUND", message="Clinic-day report was not found.", status_code=404)

        existing = self.narratives.get_for_clinic_day(clinic_day.id)
        if existing and existing.report_hash == clinic_day.report_hash and not force_regenerate:
            return NarrativeResponse(
                status=existing.status,
                summary=existing.summary_text,
                traces=existing.traces_json,
                unavailable_metrics=existing.unavailable_metrics_json,
                report_hash=existing.report_hash,
                provider=existing.provider,
                model=existing.model,
                generation_ms=existing.generation_ms,
                fallback_reason_code=existing.fallback_reason_code,
            )

        catalogue = build_fact_catalogue(clinic_day=clinic_day)
        generation_input = build_narrative_generation_input(clinic_day=clinic_day, catalogue=catalogue)
        day_type, flags = classify_day(clinic_day=clinic_day)
        status = "generated"
        provider_name: str | None = self.provider.name
        model_name: str | None = self.provider.model
        generation_ms: int | None = None
        fallback_reason_code: str | None = None
        rendered: RenderedNarrative

        try:
            provider_result = await self.provider.generate_draft(generation_input)
            provider_name = provider_result.provider
            model_name = provider_result.model
            generation_ms = provider_result.generation_ms
            try:
                rendered = validate_draft(
                    draft=provider_result.candidate,
                    catalogue=catalogue,
                    day_type=day_type,
                    flags=flags,
                )
            except GroundingValidationError as validation_error:
                try:
                    repair_result = await self.provider.generate_draft(
                        generation_input,
                        repair_feedback=[code.value for code in validation_error.codes],
                        invalid_draft=provider_result.candidate.model_dump(mode="json"),
                    )
                    provider_name = repair_result.provider
                    model_name = repair_result.model
                    generation_ms = (generation_ms or 0) + repair_result.generation_ms
                    rendered = validate_draft(
                        draft=repair_result.candidate,
                        catalogue=catalogue,
                        day_type=day_type,
                        flags=flags,
                    )
                except (NarrativeProviderError, GroundingValidationError):
                    rendered = self._fallback_rendered(clinic_day=clinic_day, catalogue=catalogue, day_type=day_type, flags=flags)
                    status = "fallback"
                    provider_name = self.provider.name if self.provider.name != "disabled" else None
                    model_name = self.provider.model
                    fallback_reason_code = "REPAIR_FAILED"
        except NarrativeProviderError as exc:
            rendered = self._fallback_rendered(clinic_day=clinic_day, catalogue=catalogue, day_type=day_type, flags=flags)
            status = "fallback"
            provider_name = self.provider.name if self.provider.name != "disabled" else None
            model_name = self.provider.model
            fallback_reason_code = self._fallback_reason(exc)
        except GroundingValidationError:
            rendered = self._fallback_rendered(clinic_day=clinic_day, catalogue=catalogue, day_type=day_type, flags=flags)
            status = "fallback"
            provider_name = self.provider.name if self.provider.name != "disabled" else None
            model_name = self.provider.model
            fallback_reason_code = "REPAIR_FAILED"
        except Exception:
            rendered = self._fallback_rendered(clinic_day=clinic_day, catalogue=catalogue, day_type=day_type, flags=flags)
            status = "fallback"
            provider_name = self.provider.name if self.provider.name != "disabled" else None
            model_name = self.provider.model
            fallback_reason_code = "GROUNDING_VALIDATION_FAILED"

        self.session.expire_all()
        current_clinic_day = self.clinic_days.get(clinic_id, business_date, with_children=True)
        if current_clinic_day is None:
            raise AppError(code="CLINIC_DAY_NOT_FOUND", message="Clinic-day report was not found.", status_code=404)
        if current_clinic_day.report_hash != generation_input.report_hash:
            raise AppError(
                code="NARRATIVE_REPORT_CHANGED",
                message="Clinic-day report changed while the narrative was being generated. Please retry.",
                status_code=409,
            )
        clinic_day = current_clinic_day

        unavailable = [item.model_dump() for item in rendered.unavailable_metrics]
        trace_payload = [trace.model_dump(mode="json") for trace in rendered.traces]
        try:
            self.narratives.save(
                clinic_day_id=clinic_day.id,
                report_hash=clinic_day.report_hash,
                status=status,
                summary_text=rendered.summary,
                traces=trace_payload,
                unavailable_metrics=unavailable,
                provider=provider_name,
                model=model_name,
                generation_ms=generation_ms,
                fallback_reason_code=fallback_reason_code,
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        return NarrativeResponse(
            status=status,
            summary=rendered.summary,
            traces=trace_payload,
            unavailable_metrics=unavailable,
            report_hash=clinic_day.report_hash,
            provider=provider_name,
            model=model_name,
            generation_ms=generation_ms,
            fallback_reason_code=fallback_reason_code,
        )

    def get(self, *, clinic_id: str, business_date) -> NarrativeResponse:
        clinic_day = self.clinic_days.get(clinic_id, business_date, with_children=True)
        if clinic_day is None:
            raise AppError(code="CLINIC_DAY_NOT_FOUND", message="Clinic-day report was not found.", status_code=404)
        narrative = self.narratives.get_for_clinic_day(clinic_day.id)
        if narrative is None:
            raise AppError(code="NARRATIVE_NOT_GENERATED", message="Narrative has not been generated.", status_code=404)
        if narrative.report_hash != clinic_day.report_hash:
            raise AppError(code="NARRATIVE_STALE", message="Narrative is stale and must be regenerated.", status_code=409)
        return NarrativeResponse(
            status=narrative.status,
            summary=narrative.summary_text,
            traces=narrative.traces_json,
            unavailable_metrics=narrative.unavailable_metrics_json,
            report_hash=narrative.report_hash,
            provider=narrative.provider,
            model=narrative.model,
            generation_ms=narrative.generation_ms,
            fallback_reason_code=narrative.fallback_reason_code,
        )

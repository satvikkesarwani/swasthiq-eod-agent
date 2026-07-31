import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.integrations.llm_provider import NarrativeProvider
from app.repositories.clinic_day_repository import ClinicDayRepository
from app.repositories.narrative_repository import NarrativeRepository
from app.schemas.narrative import (
    NarrativeCandidate,
    NarrativeResponse,
    NarrativeSectionCandidate,
    UnavailableMetric,
)
from app.services.trace_service import build_trace_catalogue, validate_and_render_candidate


class NarrativeService:
    def __init__(self, session: Session, provider: NarrativeProvider):
        self.session = session
        self.provider = provider
        self.clinic_days = ClinicDayRepository(session)
        self.narratives = NarrativeRepository(session)

    def _fallback_candidate(self, clinic_day: Any) -> NarrativeCandidate:
        report = clinic_day.report_json
        reconciliation = report["reconciliation"]
        analytics = report["analytics"]
        sections: list[NarrativeSectionCandidate] = []

        if reconciliation["total_billed_paise"] == 0 and reconciliation["total_refunds_paise"] == 0:
            sections.append(
                NarrativeSectionCandidate(
                    text_template="Good evening. No billable activity or refunds were recorded for {{metadata.business_date}}.",
                    trace_keys=["metadata.business_date"],
                )
            )
        elif reconciliation["total_billed_paise"] == 0:
            sections.append(
                NarrativeSectionCandidate(
                    text_template=(
                        "Good evening. No new sales were recorded. "
                        "{{reconciliation.refund_visit_count}} refunds totalling "
                        "{{reconciliation.total_refunds_paise}} were processed."
                    ),
                    trace_keys=[
                        "reconciliation.refund_visit_count",
                        "reconciliation.total_refunds_paise",
                    ],
                )
            )
        else:
            overview = (
                "Good evening. {{reconciliation.total_billed_paise}} was billed across "
                "{{ingestion.accepted_rows}} valid visits, and {{reconciliation.total_collected_paise}} "
                "was collected ({{reconciliation.collection_rate}})."
            )
            overview_keys = [
                "reconciliation.total_billed_paise",
                "ingestion.accepted_rows",
                "reconciliation.total_collected_paise",
                "reconciliation.collection_rate",
            ]
            if reconciliation["total_outstanding_paise"] > 0:
                overview += (
                    " {{reconciliation.total_outstanding_paise}} remains outstanding across "
                    "{{reconciliation.pending_visit_count}} visits."
                )
                overview_keys.extend([
                    "reconciliation.total_outstanding_paise",
                    "reconciliation.pending_visit_count",
                ])
            if reconciliation["total_refunds_paise"] > 0:
                overview += " Refunds totalled {{reconciliation.total_refunds_paise}}."
                overview_keys.append("reconciliation.total_refunds_paise")
            sections.append(NarrativeSectionCandidate(text_template=overview, trace_keys=overview_keys))

            if analytics["peak_hour"]:
                sections.append(
                    NarrativeSectionCandidate(
                        text_template=(
                            "The busiest hour was {{analytics.peak_hour.label}}, with "
                            "{{analytics.peak_hour.revenue_paise}} in billed revenue."
                        ),
                        trace_keys=["analytics.peak_hour.label", "analytics.peak_hour.revenue_paise"],
                    )
                )
            if analytics["top_medicines_by_quantity"]:
                sections.append(
                    NarrativeSectionCandidate(
                        text_template=(
                            "Top by quantity: {{analytics.top_medicines_by_quantity.0.drug_name}} "
                            "({{analytics.top_medicines_by_quantity.0.quantity}} units)."
                        ),
                        trace_keys=[
                            "analytics.top_medicines_by_quantity.0.drug_name",
                            "analytics.top_medicines_by_quantity.0.quantity",
                        ],
                    )
                )
            if analytics["top_medicines_by_revenue"]:
                sections.append(
                    NarrativeSectionCandidate(
                        text_template=(
                            "Top by revenue: {{analytics.top_medicines_by_revenue.0.drug_name}} "
                            "({{analytics.top_medicines_by_revenue.0.revenue_paise}})."
                        ),
                        trace_keys=[
                            "analytics.top_medicines_by_revenue.0.drug_name",
                            "analytics.top_medicines_by_revenue.0.revenue_paise",
                        ],
                    )
                )

        return NarrativeCandidate(
            sections=sections,
            unavailable_metrics=[
                UnavailableMetric(metric="profit", reason="Cost-price data was not provided, so profit cannot be calculated.")
            ],
        )

    def _required_trace_keys(self, clinic_day: Any) -> set[str]:
        report = clinic_day.report_json
        reconciliation = report["reconciliation"]
        analytics = report["analytics"]
        if reconciliation["total_billed_paise"] == 0 and reconciliation["total_refunds_paise"] == 0:
            return {"metadata.business_date"}
        if reconciliation["total_billed_paise"] == 0:
            return {"reconciliation.refund_visit_count", "reconciliation.total_refunds_paise"}

        required = {
            "reconciliation.total_billed_paise",
            "ingestion.accepted_rows",
            "reconciliation.total_collected_paise",
            "reconciliation.collection_rate",
        }
        if reconciliation["total_outstanding_paise"] > 0:
            required.update({"reconciliation.total_outstanding_paise", "reconciliation.pending_visit_count"})
        if reconciliation["total_refunds_paise"] > 0:
            required.add("reconciliation.total_refunds_paise")
        if analytics["peak_hour"]:
            required.update({"analytics.peak_hour.label", "analytics.peak_hour.revenue_paise"})
        if analytics["top_medicines_by_quantity"]:
            required.update({
                "analytics.top_medicines_by_quantity.0.drug_name",
                "analytics.top_medicines_by_quantity.0.quantity",
            })
        if analytics["top_medicines_by_revenue"]:
            required.update({
                "analytics.top_medicines_by_revenue.0.drug_name",
                "analytics.top_medicines_by_revenue.0.revenue_paise",
            })
        return required

    def _validate_complete_summary(self, clinic_day: Any, traces: list[Any]) -> None:
        used = {trace.report_path for trace in traces}
        missing = sorted(self._required_trace_keys(clinic_day) - used)
        if missing:
            raise ValueError(f"Narrative omitted required report figures: {missing}")

    @staticmethod
    def _ensure_unavailable_profit(candidate: NarrativeCandidate) -> None:
        if not any(item.metric.strip().lower() == "profit" for item in candidate.unavailable_metrics):
            candidate.unavailable_metrics.append(
                UnavailableMetric(
                    metric="profit",
                    reason="Cost-price data was not provided, so profit cannot be calculated.",
                )
            )

    def _provider_prompt(self, clinic_day: Any, catalogue: dict[str, Any]) -> str:
        safe_report = {
            "clinic_name": clinic_day.clinic_name,
            "business_date": clinic_day.business_date.isoformat(),
            "report": clinic_day.report_json,
            "available_trace_placeholders": {
                key: value.display_value for key, value in catalogue.items()
            },
        }
        return (
            "Create a short WhatsApp-appropriate owner-facing EOD summary. "
            "Use text_template placeholders exactly as listed. Every figure, medicine name, date, count, "
            "percentage, time, and money value must be a placeholder; do not type any literal digits. "
            "Do not claim profit because cost-price data is absent. Return only the required JSON schema.\n\n"
            + json.dumps(safe_report, ensure_ascii=False, sort_keys=True)
        )

    def generate(self, *, clinic_id: str, business_date, force_regenerate: bool = False) -> NarrativeResponse:
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
            )

        catalogue = build_trace_catalogue(clinic_day=clinic_day)
        candidate = None
        status = "generated"
        provider_name: str | None = self.provider.name
        model_name: str | None = self.provider.model
        last_error: Exception | None = None

        prompt = self._provider_prompt(clinic_day, catalogue)
        for attempt in range(2):
            try:
                candidate = self.provider.generate(
                    prompt=prompt,
                    repair_context=str(last_error) if attempt and last_error else None,
                )
                self._ensure_unavailable_profit(candidate)
                summary, traces = validate_and_render_candidate(candidate, catalogue)
                self._validate_complete_summary(clinic_day, traces)
                break
            except Exception as exc:
                last_error = exc
        else:
            candidate = self._fallback_candidate(clinic_day)
            summary, traces = validate_and_render_candidate(candidate, catalogue)
            self._validate_complete_summary(clinic_day, traces)
            status = "fallback"
            provider_name = self.provider.name if self.provider.name != "disabled" else None
            model_name = self.provider.model

        unavailable = [item.model_dump() for item in candidate.unavailable_metrics]
        trace_payload = [trace.model_dump(mode="json") for trace in traces]
        try:
            self.narratives.save(
                clinic_day_id=clinic_day.id,
                report_hash=clinic_day.report_hash,
                status=status,
                summary_text=summary,
                traces=trace_payload,
                unavailable_metrics=unavailable,
                provider=provider_name,
                model=model_name,
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        return NarrativeResponse(
            status=status,
            summary=summary,
            traces=trace_payload,
            unavailable_metrics=unavailable,
            report_hash=clinic_day.report_hash,
            provider=provider_name,
            model=model_name,
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
        )

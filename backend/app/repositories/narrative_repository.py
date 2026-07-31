from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Narrative


class NarrativeRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_for_clinic_day(self, clinic_day_id: str) -> Narrative | None:
        return self.session.scalar(select(Narrative).where(Narrative.clinic_day_id == clinic_day_id))

    def save(
        self,
        *,
        clinic_day_id: str,
        report_hash: str,
        status: str,
        summary_text: str,
        traces: list[dict],
        unavailable_metrics: list[dict],
        provider: str | None,
        model: str | None,
    ) -> Narrative:
        narrative = self.get_for_clinic_day(clinic_day_id)
        if narrative is None:
            narrative = Narrative(clinic_day_id=clinic_day_id, report_hash=report_hash, status=status,
                                  summary_text=summary_text, traces_json=traces,
                                  unavailable_metrics_json=unavailable_metrics,
                                  provider=provider, model=model)
            self.session.add(narrative)
        else:
            narrative.report_hash = report_hash
            narrative.status = status
            narrative.summary_text = summary_text
            narrative.traces_json = traces
            narrative.unavailable_metrics_json = unavailable_metrics
            narrative.provider = provider
            narrative.model = model
        self.session.flush()
        return narrative

import logging

from app.schemas.ingestion import PaymentMode, ValidatedVisit
from app.schemas.report import PaymentModeMetrics, ReconciliationReport

logger = logging.getLogger(__name__)


def build_reconciliation(visits: list[ValidatedVisit]) -> ReconciliationReport:
    logger.info("analysis.reconciliation.start visits=%s", len(visits))
    by_mode: dict[str, PaymentModeMetrics] = {
        mode.value: PaymentModeMetrics() for mode in PaymentMode
    }
    total_billed = 0
    total_collected = 0
    total_outstanding = 0
    total_refunds = 0
    total_discount = 0
    pending_count = 0
    refund_count = 0

    for visit in visits:
        mode = by_mode[visit.payment_mode.value]
        if visit.is_refund:
            refund = abs(visit.amount_paid_paise)
            total_refunds += refund
            refund_count += 1
            mode.refunds_paise += refund
            logger.debug(
                "analysis.reconciliation.refund visit_id=%s mode=%s refund_paise=%s",
                visit.visit_id,
                visit.payment_mode.value,
                refund,
            )
            continue

        total_billed += visit.billed_paise
        total_collected += visit.amount_paid_paise
        total_outstanding += visit.outstanding_paise
        total_discount += visit.discount_paise
        if visit.outstanding_paise > 0:
            pending_count += 1

        mode.billed_paise += visit.billed_paise
        mode.collected_paise += visit.amount_paid_paise
        mode.outstanding_paise += visit.outstanding_paise
        logger.debug(
            "analysis.reconciliation.sale visit_id=%s mode=%s billed_paise=%s collected_paise=%s outstanding_paise=%s discount_paise=%s",
            visit.visit_id,
            visit.payment_mode.value,
            visit.billed_paise,
            visit.amount_paid_paise,
            visit.outstanding_paise,
            visit.discount_paise,
        )

    collection_rate = round(total_collected / total_billed, 6) if total_billed else None
    logger.info(
        "analysis.reconciliation.done visits=%s total_billed=%s total_collected=%s total_outstanding=%s total_refunds=%s pending=%s refund_count=%s collection_rate=%s",
        len(visits),
        total_billed,
        total_collected,
        total_outstanding,
        total_refunds,
        pending_count,
        refund_count,
        collection_rate,
    )
    return ReconciliationReport(
        total_billed_paise=total_billed,
        total_collected_paise=total_collected,
        total_outstanding_paise=total_outstanding,
        total_refunds_paise=total_refunds,
        total_discount_paise=total_discount,
        collection_rate=collection_rate,
        pending_visit_count=pending_count,
        refund_visit_count=refund_count,
        by_payment_mode=by_mode,
    )

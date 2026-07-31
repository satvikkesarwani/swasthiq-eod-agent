import logging

from app.schemas.ingestion import PaymentMode, ValidatedVisit
from app.schemas.report import PaymentModeMetrics, ReconciliationReport
from app.core.money import checked_add_paise, collection_rate_basis_points

logger = logging.getLogger(__name__)


def build_reconciliation(visits: list[ValidatedVisit], *, max_safe_paise: int) -> ReconciliationReport:
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
            total_refunds = checked_add_paise(total_refunds, refund, field="total_refunds_paise", max_abs=max_safe_paise)
            refund_count += 1
            mode.refunds_paise = checked_add_paise(mode.refunds_paise, refund, field="by_payment_mode.refunds_paise", max_abs=max_safe_paise)
            logger.debug(
                "analysis.reconciliation.refund mode=%s",
                visit.payment_mode.value,
            )
            continue

        total_billed = checked_add_paise(total_billed, visit.billed_paise, field="total_billed_paise", max_abs=max_safe_paise)
        total_collected = checked_add_paise(total_collected, visit.amount_paid_paise, field="total_collected_paise", max_abs=max_safe_paise)
        total_outstanding = checked_add_paise(total_outstanding, visit.outstanding_paise, field="total_outstanding_paise", max_abs=max_safe_paise)
        total_discount = checked_add_paise(total_discount, visit.discount_paise, field="total_discount_paise", max_abs=max_safe_paise)
        if visit.outstanding_paise > 0:
            pending_count += 1

        mode.billed_paise = checked_add_paise(mode.billed_paise, visit.billed_paise, field="by_payment_mode.billed_paise", max_abs=max_safe_paise)
        mode.collected_paise = checked_add_paise(mode.collected_paise, visit.amount_paid_paise, field="by_payment_mode.collected_paise", max_abs=max_safe_paise)
        mode.outstanding_paise = checked_add_paise(mode.outstanding_paise, visit.outstanding_paise, field="by_payment_mode.outstanding_paise", max_abs=max_safe_paise)
        logger.debug(
            "analysis.reconciliation.sale mode=%s outstanding_present=%s item_count=%s",
            visit.payment_mode.value,
            visit.outstanding_paise > 0,
            len(visit.line_items),
        )

    rate_bps = collection_rate_basis_points(collected_paise=total_collected, billed_paise=total_billed)
    collection_rate = round(rate_bps / 10_000, 6) if rate_bps is not None else None
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
        collection_rate_basis_points=rate_bps,
        pending_visit_count=pending_count,
        refund_visit_count=refund_count,
        by_payment_mode=by_mode,
    )

import logging
from collections import defaultdict

from app.core.money import checked_add_paise
from app.schemas.ingestion import ValidatedVisit
from app.schemas.report import (
    AnalyticsReport,
    HourlyRevenue,
    MedicineQuantityRanking,
    MedicineRevenueRanking,
    PeakHour,
)

logger = logging.getLogger(__name__)


def build_analytics(visits: list[ValidatedVisit], *, ranking_limit: int = 5, max_safe_paise: int) -> AnalyticsReport:
    logger.info("analysis.analytics.start visits=%s ranking_limit=%s", len(visits), ranking_limit)
    hourly = {hour: 0 for hour in range(24)}
    quantity: dict[str, int] = defaultdict(int)
    revenue: dict[str, int] = defaultdict(int)

    for visit in visits:
        if visit.is_refund:
            logger.debug("analysis.analytics.skip_refund")
            continue
        hourly[visit.timestamp.hour] = checked_add_paise(hourly[visit.timestamp.hour], visit.billed_paise, field="revenue_by_hour.revenue_paise", max_abs=max_safe_paise)
        logger.debug(
            "analysis.analytics.sale hour_utc=%s items=%s",
            visit.timestamp.hour,
            len(visit.line_items),
        )
        for item in visit.line_items:
            quantity[item.drug_name_normalized] += item.qty
            revenue[item.drug_name_normalized] = checked_add_paise(
                revenue[item.drug_name_normalized],
                item.gross_revenue_paise,
                field="medicine_revenue_paise",
                max_abs=max_safe_paise,
            )

    hourly_rows = [HourlyRevenue(hour_utc=hour, revenue_paise=hourly[hour]) for hour in range(24)]
    positive_hours = [(hour, value) for hour, value in hourly.items() if value > 0]
    peak_hour = None
    if positive_hours:
        # max revenue; earliest hour wins ties.
        peak_start, peak_value = sorted(positive_hours, key=lambda item: (-item[1], item[0]))[0]
        peak_hour = PeakHour(
            start_hour_utc=peak_start,
            end_hour_utc=(peak_start + 1) % 24,
            revenue_paise=peak_value,
        )

    quantity_items = sorted(quantity.items(), key=lambda item: (-item[1], item[0]))[:ranking_limit]
    revenue_items = sorted(revenue.items(), key=lambda item: (-item[1], item[0]))[:ranking_limit]
    logger.info(
        "analysis.analytics.done visits=%s positive_hours=%s peak_hour=%s quantity_rankings=%s revenue_rankings=%s total_sales_revenue=%s",
        len(visits),
        len(positive_hours),
        peak_hour.start_hour_utc if peak_hour is not None else None,
        len(quantity_items),
        len(revenue_items),
        sum(hourly.values()),
    )

    return AnalyticsReport(
        revenue_by_hour=hourly_rows,
        peak_hour=peak_hour,
        top_medicines_by_quantity=[
            MedicineQuantityRanking(rank=index, drug_name=name, quantity=value)
            for index, (name, value) in enumerate(quantity_items, start=1)
        ],
        top_medicines_by_revenue=[
            MedicineRevenueRanking(rank=index, drug_name=name, revenue_paise=value)
            for index, (name, value) in enumerate(revenue_items, start=1)
        ],
    )

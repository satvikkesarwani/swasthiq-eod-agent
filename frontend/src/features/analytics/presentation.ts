import type { ClinicDayDetail } from "../../api/types";
import { formatCount, formatPaise } from "../../lib/formatters";
import { logDiagnostic } from "../../lib/diagnostics";
import type { AnalyticsContext, HourRevenuePoint } from "./types";

function hourLabel(hour: number): string {
  return `${String(hour).padStart(2, "0")}:00`;
}

function activityCounts(report: ClinicDayDetail) {
  return report.report.activity_counts ?? {
    accepted_visit_count: report.ingestion.accepted_rows,
    sale_visit_count: report.report.reconciliation.total_billed_paise > 0 ? Math.max(1, report.ingestion.accepted_rows - report.report.reconciliation.refund_visit_count) : 0,
    refund_visit_count: report.report.reconciliation.refund_visit_count,
    sale_line_item_count: report.report.reconciliation.total_billed_paise > 0 ? 1 : 0,
  };
}

export function formatUtcHourRange(startHour: number, endHour: number): string {
  return `${hourLabel(startHour)}-${hourLabel(endHour)} UTC`;
}

export function validateAnalyticsContract(report: ClinicDayDetail): string | null {
  const analytics = report.report.analytics;
  if (!Array.isArray(analytics.revenue_by_hour) || !Array.isArray(analytics.top_medicines_by_quantity) || !Array.isArray(analytics.top_medicines_by_revenue)) {
    return "The analytics response could not be verified.";
  }
  for (const bucket of analytics.revenue_by_hour) {
    if (!Number.isInteger(bucket.hour_utc) || bucket.hour_utc < 0 || bucket.hour_utc > 23 || !Number.isInteger(bucket.revenue_paise)) {
      return "The analytics response could not be verified.";
    }
  }
  if (analytics.peak_hour !== null) {
    const peak = analytics.peak_hour;
    if (!Number.isInteger(peak.start_hour_utc) || !Number.isInteger(peak.end_hour_utc) || !Number.isInteger(peak.revenue_paise)) {
      return "The analytics response could not be verified.";
    }
  }
  for (const item of analytics.top_medicines_by_quantity) {
    if (!Number.isInteger(item.rank) || typeof item.drug_name !== "string" || !Number.isInteger(item.quantity)) {
      return "The analytics response could not be verified.";
    }
  }
  for (const item of analytics.top_medicines_by_revenue) {
    if (!Number.isInteger(item.rank) || typeof item.drug_name !== "string" || !Number.isInteger(item.revenue_paise)) {
      return "The analytics response could not be verified.";
    }
  }
  return null;
}

export function mapHourlyRevenue(report: ClinicDayDetail): HourRevenuePoint[] {
  const peak = report.report.analytics.peak_hour;
  return report.report.analytics.revenue_by_hour.map((bucket) => {
    const rangeLabel = formatUtcHourRange(bucket.hour_utc, bucket.hour_utc + 1);
    const isPeak = peak !== null && bucket.hour_utc === peak.start_hour_utc;
    return {
      hourKey: String(bucket.hour_utc),
      displayLabel: hourLabel(bucket.hour_utc),
      rangeLabel,
      revenuePaise: bucket.revenue_paise,
      isPeak,
      accessibleLabel: `${rangeLabel}: ${formatPaise(bucket.revenue_paise)}${isPeak ? ", peak hour" : ""}`,
    };
  });
}

export function getAnalyticsContext(report: ClinicDayDetail): AnalyticsContext {
  const activity = activityCounts(report);
  if (report.ingestion.rejected_rows > 0 && report.ingestion.accepted_rows > 0) {
    logDiagnostic("info", "analytics.presentation", "Analytics context partial", {
      receivedRows: report.ingestion.received_rows,
      acceptedRows: report.ingestion.accepted_rows,
      rejectedRows: report.ingestion.rejected_rows,
    });
    return {
      kind: "partial",
      title: "Analytics use accepted rows only",
      message: `${formatCount(report.ingestion.accepted_rows)} accepted rows are included. ${formatCount(report.ingestion.rejected_rows)} rejected rows do not contribute to charts or rankings.`,
    };
  }
  if (report.ingestion.received_rows === 0 && activity.accepted_visit_count === 0) {
    logDiagnostic("warn", "analytics.presentation", "Analytics context empty day", {
      clinicId: report.clinic_id,
      businessDate: report.business_date,
      receivedRows: report.ingestion.received_rows,
      acceptedRows: report.ingestion.accepted_rows,
    });
    return { kind: "empty", title: "No billing activity", message: "No billing activity was recorded for this clinic day." };
  }
  if (activity.sale_visit_count === 0 && activity.refund_visit_count > 0) {
    logDiagnostic("info", "analytics.presentation", "Analytics context refund only", {
      refundVisitCount: activity.refund_visit_count,
    });
    return { kind: "refund_only", title: "Refund-only day", message: "No new sales were recorded. Refund activity is available in Reconciliation." };
  }
  if (activity.sale_visit_count > 0 && activity.refund_visit_count > 0) {
    logDiagnostic("info", "analytics.presentation", "Analytics context sales and refunds", {
      saleVisitCount: activity.sale_visit_count,
      refundVisitCount: activity.refund_visit_count,
    });
    return { kind: "sales_and_refunds", title: "Sales analytics exclude refund entries", message: "Refund totals remain available in Reconciliation." };
  }
  if (activity.sale_visit_count > 0) {
    logDiagnostic("info", "analytics.presentation", "Analytics context sales", {
      saleVisitCount: activity.sale_visit_count,
    });
    return { kind: "sales", title: "Sales analytics loaded", message: "Charts and rankings use accepted non-refund sales from the deterministic report." };
  }
  logDiagnostic("warn", "analytics.presentation", "Analytics context no accepted sales", {
    receivedRows: report.ingestion.received_rows,
    acceptedRows: report.ingestion.accepted_rows,
    rejectedRows: report.ingestion.rejected_rows,
    saleVisitCount: activity.sale_visit_count,
    refundVisitCount: activity.refund_visit_count,
  });
  return { kind: "no_sales", title: "No accepted sales analytics", message: "No accepted sales rows were available for analytics." };
}

export function peakPresentation(report: ClinicDayDetail): { title: string; hour: string; amount: string; explanation: string } {
  const peak = report.report.analytics.peak_hour;
  if (peak === null) {
    const context = getAnalyticsContext(report);
    return {
      title: "No sales peak available",
      hour: "Not applicable",
      amount: "No peak amount",
      explanation: context.kind === "refund_only" ? "Refund activity is shown in Reconciliation." : "No accepted billed sales were available for a peak-hour observation.",
    };
  }
  return {
    title: "Peak Billing Hour",
    hour: formatUtcHourRange(peak.start_hour_utc, peak.end_hour_utc),
    amount: formatPaise(peak.revenue_paise),
    explanation: "Highest backend-recorded hourly billed-sales bucket.",
  };
}

export function quantityUnit(value: number): string {
  return `${formatCount(value)} ${value === 1 ? "unit" : "units"}`;
}

export function shortHash(value: string): string {
  return value.slice(0, 12);
}

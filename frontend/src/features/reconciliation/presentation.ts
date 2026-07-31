import { isValidBusinessDate, isValidClinicId } from "../../app/routes";
import type { ClinicDayDetail } from "../../api/types";
import type { CollectionHealth, DayActivity, MetricDefinition, PaymentModeKey } from "./types";

const PAYMENT_MODE_ORDER: PaymentModeKey[] = ["cash", "card", "upi"];

function activityCounts(report: ClinicDayDetail) {
  return report.report.activity_counts ?? {
    accepted_visit_count: report.ingestion.accepted_rows,
    sale_visit_count: report.report.reconciliation.total_billed_paise > 0 ? Math.max(1, report.ingestion.accepted_rows - report.report.reconciliation.refund_visit_count) : 0,
    refund_visit_count: report.report.reconciliation.refund_visit_count,
    sale_line_item_count: report.report.reconciliation.total_billed_paise > 0 ? 1 : 0,
  };
}

export function validateReportParams(params: { clinicId?: string; businessDate?: string }): { clinicId: string; businessDate: string } | null {
  if (!isValidClinicId(params.clinicId) || !isValidBusinessDate(params.businessDate)) {
    return null;
  }
  return { clinicId: params.clinicId.trim(), businessDate: params.businessDate };
}

export function mapMetrics(report: ClinicDayDetail): MetricDefinition[] {
  const reconciliation = report.report.reconciliation;
  return [
    {
      key: "billed",
      label: "Total Billed",
      valuePaise: reconciliation.total_billed_paise,
      accent: "neutral",
      description: "Value billed after recorded discounts",
    },
    {
      key: "collected",
      label: "Total Collected",
      valuePaise: reconciliation.total_collected_paise,
      accent: "success",
      description: "Amount collected from accepted sales",
    },
    {
      key: "outstanding",
      label: "Outstanding",
      valuePaise: reconciliation.total_outstanding_paise,
      accent: reconciliation.total_outstanding_paise > 0 ? "warning" : "success",
      description: "Amount still pending collection",
    },
    {
      key: "refunds",
      label: "Refunds",
      valuePaise: reconciliation.total_refunds_paise,
      accent: "refund",
      description: "Money returned through refund entries",
    },
  ];
}

export function orderPaymentModes(report: ClinicDayDetail) {
  const rows = report.report.reconciliation.by_payment_mode;
  const knownRows = PAYMENT_MODE_ORDER.flatMap((mode) => {
    const row = rows[mode];
    return row ? [{ mode, metrics: row }] : [];
  });
  const unknownRows = Object.entries(rows)
    .filter(([mode]) => !PAYMENT_MODE_ORDER.includes(mode as PaymentModeKey))
    .map(([mode, metrics]) => ({ mode, metrics }));
  return [...knownRows, ...unknownRows];
}

export function getCollectionHealth(report: ClinicDayDetail): CollectionHealth {
  const reconciliation = report.report.reconciliation;
  const activity = activityCounts(report);
  if (activity.sale_visit_count === 0 && activity.refund_visit_count > 0) {
    return {
      label: "Refund activity only",
      tone: "fallback",
      description: "No new sales were recorded. Refund activity is shown separately.",
    };
  }
  if (activity.sale_visit_count === 0) {
    return {
      label: "No sales collection required",
      tone: "neutral",
      description: "No billed sales were recorded for this clinic day.",
    };
  }
  if (reconciliation.total_outstanding_paise > 0) {
    return {
      label: "Collection pending",
      tone: "warning",
      description: "Backend totals show a pending amount for accepted sales.",
    };
  }
  return {
    label: "Fully collected",
    tone: "healthy",
    description: "Backend totals show no outstanding amount for accepted sales.",
  };
}

export function getDayActivity(report: ClinicDayDetail): DayActivity {
  const activity = activityCounts(report);
  if (report.ingestion.rejected_rows > 0 && report.ingestion.accepted_rows > 0) {
    return {
      kind: "partial",
      label: "Report generated from accepted rows",
      description: "Rejected rows are excluded from all totals and analytics.",
    };
  }
  if (report.ingestion.received_rows === 0 && activity.accepted_visit_count === 0) {
    return {
      kind: "empty",
      label: "No activity recorded",
      description: "No billing, collection or refund activity was recorded for this clinic day.",
    };
  }
  if (activity.sale_visit_count === 0 && activity.refund_visit_count > 0) {
    return {
      kind: "refund_only",
      label: "Refund-only day",
      description: "No new sales were recorded. Refund activity is shown separately.",
    };
  }
  if (activity.sale_visit_count > 0 && activity.refund_visit_count > 0) {
    return {
      kind: "sales_and_refunds",
      label: "Sales and refunds recorded",
      description: "Sales and refund activity were both recorded.",
    };
  }
  if (activity.sale_visit_count > 0) {
    return {
      kind: "sales",
      label: "Sales activity recorded",
      description: "Accepted sales rows produced this deterministic reconciliation.",
    };
  }
  return {
    kind: "unknown",
    label: "Report loaded",
    description: "Financial totals on this page come from the deterministic billing report.",
  };
}

export function formatCollectionRate(value: number | null): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "Not applicable";
  }
  return `${(value * 100).toFixed(1)}%`;
}

export function collectionRateVisualPercent(value: number | null): number {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(100, value * 100));
}

export function reportHashPrefix(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  return value.slice(0, 12);
}

export function importNotice(operation: string | null | undefined): string | null {
  switch (operation) {
    case "created":
      return "Clinic-day report created successfully.";
    case "replaced":
      return "Clinic-day report replaced successfully.";
    case "unchanged":
      return "The submitted billing log produced the same deterministic report.";
    default:
      return null;
  }
}

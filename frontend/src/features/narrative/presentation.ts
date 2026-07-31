import type { ClinicDayDetail, NarrativeResponse } from "../../api/types";
import { formatBusinessDate, formatCount, safeLabel } from "../../lib/formatters";

export function validateNarrativeContract(narrative: NarrativeResponse): string | null {
  if (typeof narrative.summary !== "string" || narrative.summary.trim().length === 0) {
    return "The summary response could not be verified.";
  }
  if (!Array.isArray(narrative.traces) || !Array.isArray(narrative.unavailable_metrics)) {
    return "The summary response could not be verified.";
  }
  if (/\d/.test(narrative.summary) && narrative.traces.length === 0) {
    return "The summary response could not be verified.";
  }
  for (const trace of narrative.traces) {
    if (typeof trace.display_value !== "string" || typeof trace.report_path !== "string") {
      return "The summary response could not be verified.";
    }
  }
  for (const metric of narrative.unavailable_metrics) {
    if (typeof metric.metric !== "string" || typeof metric.reason !== "string") {
      return "The summary response could not be verified.";
    }
  }
  return null;
}

export function narrativeStatusLabel(narrative: NarrativeResponse | null, source: "cached" | "generated" | null): string {
  if (!narrative) {
    return "Not generated";
  }
  if (source === "cached") {
    return "Cached summary";
  }
  if (narrative.status === "fallback") {
    return "Deterministic fallback";
  }
  return "Generated summary";
}

export function narrativeStatusTone(narrative: NarrativeResponse | null): "neutral" | "healthy" | "fallback" | "warning" {
  if (!narrative) {
    return "neutral";
  }
  if (narrative.status === "fallback") {
    return "fallback";
  }
  if (narrative.status === "generated") {
    return "healthy";
  }
  return "warning";
}

export function fallbackReasonLabel(code: string | null | undefined): string {
  switch (code) {
    case "LLM_DISABLED":
      return "Provider disabled";
    case "PROVIDER_NOT_CONFIGURED":
      return "Provider not configured";
    case "PROVIDER_AUTHENTICATION_FAILED":
      return "Provider authentication failed";
    case "PROVIDER_RATE_LIMITED":
      return "Provider rate limited";
    case "PROVIDER_TIMEOUT":
      return "Provider timeout";
    case "PROVIDER_UNAVAILABLE":
      return "Provider unavailable";
    case "PROVIDER_INVALID_RESPONSE":
      return "Provider response could not be validated";
    case "REPAIR_FAILED":
      return "Repair failed";
    case "GROUNDING_VALIDATION_FAILED":
      return "Grounding validation failed";
    default:
      return code ? "Fallback used" : "Not applicable";
  }
}

export function reportHashPrefix(value: string): string {
  return value.slice(0, 12);
}

export function traceLabel(reportPath: string): string {
  const leaf = reportPath.split(".").filter(Boolean).at(-1) ?? reportPath;
  return leaf.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function rawValueLabel(value: unknown): string {
  if (value === null || value === undefined) {
    return "Not available";
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "Structured value";
}

export function narrativeContext(report: ClinicDayDetail): { title: string; message: string; kind: "partial" | "empty" | "refund_only" | "warning" | "sales" } {
  const reconciliation = report.report.reconciliation;
  if (report.ingestion.rejected_rows > 0 && report.ingestion.accepted_rows > 0) {
    return {
      kind: "partial",
      title: "Summary uses accepted rows only",
      message: `${formatCount(report.ingestion.accepted_rows)} accepted rows are included. ${formatCount(report.ingestion.rejected_rows)} rejected rows are excluded from every figure.`,
    };
  }
  if (report.ingestion.received_rows === 0 && reconciliation.total_billed_paise === 0 && reconciliation.total_refunds_paise === 0) {
    return { kind: "empty", title: "Empty clinic day", message: "The summary should state that no billing, collection or refund activity was recorded." };
  }
  if (reconciliation.total_billed_paise === 0 && reconciliation.total_refunds_paise > 0) {
    return { kind: "refund_only", title: "Refund-only day", message: "The summary should avoid sales peaks and medicine rankings, and keep refunds separate." };
  }
  if (report.report.data_quality_warnings.length > 0) {
    return { kind: "warning", title: "Data-quality context available", message: "Backend warnings remain advisory and do not alter reported figures." };
  }
  return { kind: "sales", title: "Grounded owner summary", message: "The summary is generated from the deterministic report and validated traces." };
}

export function copySummaryText(report: ClinicDayDetail, narrative: NarrativeResponse): string {
  const clinic = safeLabel(report.clinic_name, report.clinic_id);
  return `EOD Summary - ${clinic} - ${formatBusinessDate(report.business_date)}\n\n${narrative.summary}`;
}

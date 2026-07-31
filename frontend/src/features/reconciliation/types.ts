import type { ClinicDayDetail } from "../../api/types";

export type ReconciliationLoaderData =
  | { state: "ready"; report: ClinicDayDetail }
  | { state: "not_found"; clinicId: string; businessDate: string }
  | { state: "error"; clinicId: string; businessDate: string; title: string; message: string; requestId: string | null };

export type PaymentModeKey = "cash" | "card" | "upi";

export type MetricAccent = "neutral" | "success" | "warning" | "refund";

export type MetricDefinition = {
  key: "billed" | "collected" | "outstanding" | "refunds";
  label: string;
  valuePaise: number;
  accent: MetricAccent;
  description: string;
};

export type CollectionHealth = {
  label: string;
  tone: "healthy" | "warning" | "neutral" | "fallback";
  description: string;
};

export type DayActivity = {
  kind: "empty" | "refund_only" | "sales_and_refunds" | "sales" | "partial" | "unknown";
  label: string;
  description: string;
};

export type ImportNavigationState = {
  operation?: string;
  status?: string;
  acceptedRows?: number;
  rejectedRows?: number;
};

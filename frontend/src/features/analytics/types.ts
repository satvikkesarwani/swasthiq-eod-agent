import type { ClinicDayDetail } from "../../api/types";

export type AnalyticsLoaderData =
  | { state: "ready"; report: ClinicDayDetail }
  | { state: "not_found"; clinicId: string; businessDate: string }
  | { state: "error"; clinicId: string; businessDate: string; title: string; message: string; requestId: string | null };

export type HourRevenuePoint = {
  hourKey: string;
  displayLabel: string;
  rangeLabel: string;
  revenuePaise: number;
  isPeak: boolean;
  accessibleLabel: string;
};

export type AnalyticsContext = {
  kind: "partial" | "empty" | "refund_only" | "sales_and_refunds" | "sales" | "no_sales";
  title: string;
  message: string;
};

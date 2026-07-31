import type { components } from "./generated/schema";

export type HealthResponse = components["schemas"]["HealthResponse"];
export type ClinicDaySummary = components["schemas"]["ClinicDayListItem"];
export type ClinicDayListResponse = components["schemas"]["ClinicDayListResponse"];
export type ClinicDayDetail = components["schemas"]["ClinicDayResponse"];
export type BillingLogRequest = {
  records: unknown[];
  clinic_name?: string | null;
  clinic_location?: string | null;
};
export type IngestionIssue = components["schemas"]["IngestionIssue"];
export type IngestionIssueListResponse = components["schemas"]["IngestionIssueListResponse"];
export type NarrativeResponse = components["schemas"]["NarrativeResponse"];
export type NarrativeGenerateRequest = components["schemas"]["NarrativeGenerateRequest"];
export type ApiErrorPayload = components["schemas"]["ErrorResponse"];

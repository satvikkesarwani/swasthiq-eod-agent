import { apiUrl, requestJson, type ApiRequestOptions } from "./client";
import type {
  BillingLogRequest,
  ClinicDayDetail,
  ClinicDayListResponse,
  HealthResponse,
  IngestionIssueListResponse,
  NarrativeGenerateRequest,
  NarrativeResponse,
} from "./types";

function encoded(value: string): string {
  return encodeURIComponent(value);
}

function appendOptional(params: URLSearchParams, key: string, value: string | number | undefined): void {
  if (value !== undefined && value !== "") {
    params.set(key, String(value));
  }
}

function requestOptions(signal?: AbortSignal, method?: "GET" | "POST" | "PUT", body?: unknown): ApiRequestOptions {
  return {
    ...(method !== undefined ? { method } : {}),
    ...(body !== undefined ? { body } : {}),
    ...(signal !== undefined ? { signal } : {}),
  };
}

export function healthUrl(): string {
  return apiUrl("/health");
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health", requestOptions(signal));
}

export function listClinicDays(params: {
  clinicId?: string;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
  offset?: number;
} = {}, signal?: AbortSignal): Promise<ClinicDayListResponse> {
  const query = new URLSearchParams();
  appendOptional(query, "clinic_id", params.clinicId);
  appendOptional(query, "date_from", params.dateFrom);
  appendOptional(query, "date_to", params.dateTo);
  appendOptional(query, "limit", params.limit);
  appendOptional(query, "offset", params.offset);
  return requestJson<ClinicDayListResponse>(`/clinic-days${query.size ? `?${query.toString()}` : ""}`, requestOptions(signal));
}

export function getClinicDay(clinicId: string, businessDate: string, signal?: AbortSignal): Promise<ClinicDayDetail> {
  return requestJson<ClinicDayDetail>(`/clinic-days/${encoded(clinicId)}/${encoded(businessDate)}`, requestOptions(signal));
}

export function putClinicDay(
  clinicId: string,
  businessDate: string,
  input: BillingLogRequest,
  signal?: AbortSignal,
): Promise<ClinicDayDetail> {
  return requestJson<ClinicDayDetail>(`/clinic-days/${encoded(clinicId)}/${encoded(businessDate)}`, requestOptions(signal, "PUT", input));
}

export function getClinicDayErrors(
  clinicId: string,
  businessDate: string,
  params: { limit?: number; offset?: number } = {},
  signal?: AbortSignal,
): Promise<IngestionIssueListResponse> {
  const query = new URLSearchParams();
  appendOptional(query, "limit", params.limit);
  appendOptional(query, "offset", params.offset);
  return requestJson<IngestionIssueListResponse>(
    `/clinic-days/${encoded(clinicId)}/${encoded(businessDate)}/errors${query.size ? `?${query.toString()}` : ""}`,
    requestOptions(signal),
  );
}

export function getNarrative(clinicId: string, businessDate: string, signal?: AbortSignal): Promise<NarrativeResponse> {
  return requestJson<NarrativeResponse>(`/clinic-days/${encoded(clinicId)}/${encoded(businessDate)}/narrative`, requestOptions(signal));
}

export function generateNarrative(
  clinicId: string,
  businessDate: string,
  input: NarrativeGenerateRequest = { force_regenerate: false },
  signal?: AbortSignal,
): Promise<NarrativeResponse> {
  return requestJson<NarrativeResponse>(
    `/clinic-days/${encoded(clinicId)}/${encoded(businessDate)}/narrative`,
    requestOptions(signal, "POST", input),
  );
}

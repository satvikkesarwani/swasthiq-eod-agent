import { isValidBusinessDateInput } from "../import/validation";

export const RECENT_REPORTS_LIMIT = 10;

export type ReportsQuery = {
  clinicId?: string | undefined;
  dateFrom?: string | undefined;
  dateTo?: string | undefined;
  limit: number;
  offset: number;
  rangeError: string | null;
};

function positiveInt(value: string | null, fallback: number): number {
  if (value === null) {
    return fallback;
  }
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed < 0) {
    return fallback;
  }
  return parsed;
}

export function parseReportsQuery(search: string): ReportsQuery {
  const params = new URLSearchParams(search);
  const clinicId = params.get("clinic_id")?.trim() || undefined;
  const dateFromRaw = params.get("date_from")?.trim();
  const dateToRaw = params.get("date_to")?.trim();
  const dateFrom = dateFromRaw && isValidBusinessDateInput(dateFromRaw) ? dateFromRaw : undefined;
  const dateTo = dateToRaw && isValidBusinessDateInput(dateToRaw) ? dateToRaw : undefined;
  const limit = Math.min(RECENT_REPORTS_LIMIT, positiveInt(params.get("limit"), RECENT_REPORTS_LIMIT) || RECENT_REPORTS_LIMIT);
  const offset = positiveInt(params.get("offset"), 0);
  const rangeError = dateFrom && dateTo && dateFrom > dateTo ? "Date from cannot be after date to." : null;
  return {
    ...(clinicId ? { clinicId } : {}),
    ...(dateFrom ? { dateFrom } : {}),
    ...(dateTo ? { dateTo } : {}),
    limit,
    offset,
    rangeError,
  };
}

export function reportsQueryToSearch(query: Partial<ReportsQuery>): string {
  const params = new URLSearchParams();
  if (query.clinicId) {
    params.set("clinic_id", query.clinicId);
  }
  if (query.dateFrom) {
    params.set("date_from", query.dateFrom);
  }
  if (query.dateTo) {
    params.set("date_to", query.dateTo);
  }
  if (query.limit && query.limit !== RECENT_REPORTS_LIMIT) {
    params.set("limit", String(query.limit));
  }
  if (query.offset && query.offset > 0) {
    params.set("offset", String(query.offset));
  }
  return params.toString();
}

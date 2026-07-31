const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export function reportsHomePath(): string {
  return "/reports";
}

function encoded(value: string): string {
  return encodeURIComponent(value.trim());
}

export function isValidClinicId(value: string | undefined): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

export function isValidBusinessDate(value: string | undefined): value is string {
  if (typeof value !== "string" || !DATE_RE.test(value)) {
    return false;
  }
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

export function reconciliationPath(clinicId: string, businessDate: string): string {
  return `/reports/${encoded(clinicId)}/${encoded(businessDate)}/reconciliation`;
}

export function analyticsPath(clinicId: string, businessDate: string): string {
  return `/reports/${encoded(clinicId)}/${encoded(businessDate)}/analytics`;
}

export function narrativePath(clinicId: string, businessDate: string): string {
  return `/reports/${encoded(clinicId)}/${encoded(businessDate)}/narrative`;
}

export function hasValidReportParams(params: { clinicId?: string; businessDate?: string }): boolean {
  return isValidClinicId(params.clinicId) && isValidBusinessDate(params.businessDate);
}

export const reportRoutes = {
  reports: reportsHomePath,
  reconciliation: reconciliationPath,
  analytics: analyticsPath,
  narrative: narrativePath,
} as const;

export function formatPaise(value: number): string {
  if (!Number.isFinite(value)) {
    return "₹0";
  }
  const sign = value < 0 ? "-" : "";
  const absolute = Math.abs(Math.trunc(value));
  const rupees = Math.floor(absolute / 100);
  const paise = absolute % 100;
  const grouped = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(rupees);
  return paise === 0 ? `${sign}₹${grouped}` : `${sign}₹${grouped}.${String(paise).padStart(2, "0")}`;
}

export function formatCount(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "0";
  }
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(Math.trunc(value));
}

export function formatBusinessDate(value: string | null | undefined): string {
  if (!value) {
    return "Date unavailable";
  }
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }).format(date);
}

export function formatUtcHourRange(startHour: number, endHour: number): string {
  if (!Number.isInteger(startHour) || !Number.isInteger(endHour) || startHour < 0 || startHour > 23 || endHour < 0 || endHour > 23) {
    return "Hour unavailable";
  }
  const label = (hour: number) => `${String(hour).padStart(2, "0")}:00`;
  return `${label(startHour)}-${label(endHour)} UTC`;
}

export function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "Not available";
  }
  return `${(value * 100).toFixed(1)}%`;
}

export function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return "0 B";
  }
  if (bytes < 1024) {
    return `${Math.trunc(bytes)} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function safeLabel(value: string | null | undefined, fallback = "Unavailable"): string {
  const trimmed = value?.trim();
  return trimmed && trimmed.length > 0 ? trimmed : fallback;
}

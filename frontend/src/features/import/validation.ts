import { formatFileSize } from "../../lib/formatters";
import { BACKEND_REQUEST_LIMIT_BYTES, BILLING_FILE_LIMIT_LABEL, MAX_BILLING_FILE_BYTES } from "./constants";
import type { BillingFileError } from "./types";

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const DISPLAY_DATE_RE = /^(\d{2})\/(\d{2})\/(\d{4})$/;

export function validateBillingFile(file: File): BillingFileError | null {
  const name = file.name.trim();
  if (!name.toLowerCase().endsWith(".json")) {
    return {
      code: "UNSUPPORTED_FILE",
      message: "Choose a JSON file with the .json extension.",
    };
  }

  if (file.size > MAX_BILLING_FILE_BYTES) {
    return {
      code: "FILE_TOO_LARGE",
      message: `The selected file is ${formatFileSize(file.size)}. The frontend accepts files up to ${BILLING_FILE_LIMIT_LABEL}; the service request limit is ${formatFileSize(BACKEND_REQUEST_LIMIT_BYTES)}.`,
    };
  }

  return null;
}

export function validateDroppedFiles(files: FileList | File[]): BillingFileError | null {
  if (files.length === 0) {
    return { code: "NO_FILE", message: "Choose one JSON billing log." };
  }
  if (files.length > 1) {
    return { code: "MULTIPLE_FILES", message: "Drop exactly one JSON billing log." };
  }
  const [file] = files;
  return file ? validateBillingFile(file) : { code: "NO_FILE", message: "Choose one JSON billing log." };
}

export function isValidBusinessDateInput(value: string): boolean {
  return normalizeBusinessDateInput(value) !== null;
}

export function normalizeBusinessDateInput(value: string): string | null {
  const trimmed = value.trim();
  const displayMatch = DISPLAY_DATE_RE.exec(trimmed);
  const candidate = displayMatch
    ? `${displayMatch[3]}-${displayMatch[2]}-${displayMatch[1]}`
    : trimmed;

  if (!DATE_RE.test(candidate)) {
    return null;
  }
  const date = new Date(`${candidate}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === candidate ? candidate : null;
}

export function trimOptional(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

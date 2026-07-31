type DiagnosticLevel = "debug" | "info" | "warn" | "error";

type DiagnosticData = Record<string, unknown>;

const PREFIX = "[SwasthiQ]";
const MAX_EVENTS = 500;

declare global {
  interface Window {
    __SWASTHIQ_DIAGNOSTICS__?: Array<DiagnosticData>;
  }
}

function diagnosticsEnabled(): boolean {
  if (import.meta.env.DEV) {
    return true;
  }
  try {
    return globalThis.localStorage?.getItem("swasthiq:diagnostics") === "1";
  } catch {
    return false;
  }
}

function scrub(value: unknown): unknown {
  if (Array.isArray(value)) {
    return { arrayLength: value.length };
  }
  if (value instanceof Error) {
    return { name: value.name, message: value.message };
  }
  if (typeof value !== "object" || value === null) {
    return value;
  }
  return Object.fromEntries(
    Object.entries(value as DiagnosticData).map(([key, entry]) => {
      if (key.toLowerCase().includes("records") && Array.isArray(entry)) {
        return [key, { arrayLength: entry.length }];
      }
      return [key, scrub(entry)];
    }),
  );
}

export function logDiagnostic(level: DiagnosticLevel, scope: string, message: string, data: DiagnosticData = {}): void {
  if (!diagnosticsEnabled()) {
    return;
  }
  const payload = {
    scope,
    level,
    message,
    at: new Date().toISOString(),
    ...scrub(data) as DiagnosticData,
  };
  if (typeof window !== "undefined") {
    window.__SWASTHIQ_DIAGNOSTICS__ = [...(window.__SWASTHIQ_DIAGNOSTICS__ ?? []), payload].slice(-MAX_EVENTS);
  }
  const logger = console[level] ?? console.log;
  logger(`${PREFIX} ${message} ${JSON.stringify(payload)}`);
}

export function logGlobalDiagnostics(): void {
  if (!diagnosticsEnabled() || typeof window === "undefined") {
    return;
  }
  window.addEventListener("error", (event) => {
    logDiagnostic("error", "window", "Unhandled browser error", {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    });
  });
  window.addEventListener("unhandledrejection", (event) => {
    logDiagnostic("error", "window", "Unhandled promise rejection", {
      reason: event.reason,
    });
  });
}

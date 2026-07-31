import { logEvent } from "./logger";

type DiagnosticLevel = "debug" | "info" | "warn" | "error";

type DiagnosticData = Record<string, unknown>;

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

export function logDiagnostic(level: DiagnosticLevel, scope: string, message: string, data: DiagnosticData = {}): void {
  if (!diagnosticsEnabled()) {
    return;
  }
  const payload = logEvent(level, scope, message, data);
  if (!payload) {
    return;
  }
  if (typeof window !== "undefined") {
    window.__SWASTHIQ_DIAGNOSTICS__ = [...(window.__SWASTHIQ_DIAGNOSTICS__ ?? []), payload].slice(-MAX_EVENTS);
  }
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

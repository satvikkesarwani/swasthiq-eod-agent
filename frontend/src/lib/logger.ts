type LogLevel = "debug" | "info" | "warn" | "error";

type LogData = Record<string, unknown>;

const SENSITIVE_KEYS = ["authorization", "api_key", "token", "secret", "password", "cookie", "records", "summary", "narrative", "clipboard"];

function shouldLog(level: LogLevel): boolean {
  if (import.meta.env.DEV) {
    return true;
  }
  if (level === "debug") {
    return false;
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
    Object.entries(value as LogData).map(([key, entry]) => {
      const lower = key.toLowerCase();
      if (SENSITIVE_KEYS.some((pattern) => lower.includes(pattern))) {
        return [key, "[redacted]"];
      }
      return [key, scrub(entry)];
    }),
  );
}

export function logEvent(level: LogLevel, scope: string, message: string, data: LogData = {}): LogData | null {
  if (!shouldLog(level)) {
    return null;
  }
  const payload = {
    scope,
    level,
    message,
    at: new Date().toISOString(),
    ...(scrub(data) as LogData),
  };
  const rendered = `[SwasthiQ] ${message} ${JSON.stringify(payload)}`;
  switch (level) {
    case "debug":
      console.debug(rendered);
      break;
    case "info":
      console.info(rendered);
      break;
    case "warn":
      console.warn(rendered);
      break;
    case "error":
      console.error(rendered);
      break;
  }
  return payload;
}

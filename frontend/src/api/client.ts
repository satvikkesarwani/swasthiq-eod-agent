import type { ApiErrorPayload } from "./types";
import { logDiagnostic } from "../lib/diagnostics";
import { stringifySafeJson } from "../features/import/jsonSafety";

const API_PREFIX = "/api/v1";
export const API_OK_EVENT = "swasthiq:api-ok";

export type ApiRequestOptions = {
  method?: "GET" | "POST" | "PUT";
  body?: unknown;
  signal?: AbortSignal;
};

type RuntimeEnv = {
  DEV?: boolean;
  VITE_API_BASE_URL?: string;
};

function runtimeEnv(): RuntimeEnv {
  return ((import.meta as ImportMeta & { env?: RuntimeEnv }).env ?? {});
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;
  readonly details: unknown[];

  constructor(message: string, status: number, code: string, requestId: string | null, details: unknown[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
    this.details = details;
  }
}

export function normalizeApiBase(rawBase?: string): string {
  const envBase = runtimeEnv().VITE_API_BASE_URL;
  const candidate = rawBase ?? envBase ?? "";
  const trimmed = candidate.trim().replace(/\/+$/, "");
  return trimmed.endsWith(API_PREFIX) ? trimmed.slice(0, -API_PREFIX.length) : trimmed;
}

export function apiUrl(path: string, query?: URLSearchParams): string {
  const base = normalizeApiBase();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const qs = query && [...query.keys()].length > 0 ? `?${query.toString()}` : "";
  return `${base}${API_PREFIX}${normalizedPath}${qs}`;
}

function localDevFallbackUrl(path: string, query?: URLSearchParams): string | null {
  const env = runtimeEnv();
  if (env.VITE_API_BASE_URL || !env.DEV || typeof window === "undefined") {
    return null;
  }
  if (!["localhost", "127.0.0.1"].includes(window.location.hostname)) {
    return null;
  }
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const qs = query && [...query.keys()].length > 0 ? `?${query.toString()}` : "";
  return `http://127.0.0.1:8000${API_PREFIX}${normalizedPath}${qs}`;
}

function apiUrlCandidates(path: string, query?: URLSearchParams): string[] {
  const primary = apiUrl(path, query);
  const fallback = localDevFallbackUrl(path, query);
  return fallback && fallback !== primary ? [primary, fallback] : [primary];
}

function headersFromXhr(rawHeaders: string): Headers {
  const headers = new Headers();
  for (const line of rawHeaders.trim().split(/[\r\n]+/)) {
    const separator = line.indexOf(":");
    if (separator > 0) {
      headers.append(line.slice(0, separator).trim(), line.slice(separator + 1).trim());
    }
  }
  return headers;
}

function requestWithXhr(url: string, init: RequestInit): Promise<Response> {
  return new Promise((resolve, reject) => {
    if (typeof XMLHttpRequest === "undefined") {
      reject(new TypeError("No browser HTTP transport is available."));
      return;
    }
    const xhr = new XMLHttpRequest();
    const method = init.method ?? "GET";
    xhr.open(method, url, true);
    xhr.responseType = "text";
    xhr.withCredentials = init.credentials === "include";

    if (init.headers instanceof Headers) {
      init.headers.forEach((value, key) => xhr.setRequestHeader(key, value));
    }

    const abort = () => {
      xhr.abort();
      reject(new DOMException("The request was aborted.", "AbortError"));
    };
    init.signal?.addEventListener("abort", abort, { once: true });
    xhr.addEventListener("load", () => {
      init.signal?.removeEventListener("abort", abort);
      resolve(new Response(xhr.responseText, {
        status: xhr.status,
        statusText: xhr.statusText,
        headers: headersFromXhr(xhr.getAllResponseHeaders()),
      }));
    });
    xhr.addEventListener("error", () => {
      init.signal?.removeEventListener("abort", abort);
      reject(new TypeError("XMLHttpRequest network request failed."));
    });
    xhr.addEventListener("timeout", () => {
      init.signal?.removeEventListener("abort", abort);
      reject(new TypeError("XMLHttpRequest timed out."));
    });
    xhr.send(typeof init.body === "string" ? init.body : null);
  });
}

async function sendHttpRequest(url: string, init: RequestInit): Promise<Response> {
  if (typeof fetch === "function") {
    logDiagnostic("debug", "api", "Using fetch transport", { url });
    return fetch(url, init);
  }
  logDiagnostic("warn", "api", "Fetch transport missing; using XMLHttpRequest fallback", { url });
  return requestWithXhr(url, init);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function parseJson(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return undefined;
  }
  const text = await response.text();
  if (text.length === 0) {
    return undefined;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw new ApiError("The server returned malformed JSON.", response.status, "MALFORMED_JSON", null);
  }
}

function toApiError(payload: unknown, status: number, fallbackRequestId: string | null): ApiError {
  const envelope = payload as Partial<ApiErrorPayload>;
  const body = isRecord(envelope.error) ? envelope.error : null;
  const code = typeof body?.code === "string" ? body.code : "HTTP_ERROR";
  const message = typeof body?.message === "string" ? body.message : "The server request failed.";
  const requestId = typeof body?.request_id === "string" ? body.request_id : fallbackRequestId;
  const details = Array.isArray(body?.details) ? body.details : [];
  return new ApiError(message, status, code, requestId, details);
}

export async function requestJson<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const startedAt = performance.now();
  const headers = new Headers({ Accept: "application/json" });
  let body: string | undefined;
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = stringifySafeJson(options.body);
  }

  let response: Response | undefined;
  try {
    const init: RequestInit = {
      method: options.method ?? "GET",
      headers,
      credentials: "same-origin",
    };
    if (body !== undefined) {
      init.body = body;
    }
    if (options.signal !== undefined) {
      init.signal = options.signal;
    }
    const urls = apiUrlCandidates(path);
    logDiagnostic("info", "api", "Request start", {
      method: init.method,
      path,
      urls,
      hasBody: body !== undefined,
      bodyBytes: body?.length ?? 0,
    });
    for (const [index, url] of urls.entries()) {
      try {
        logDiagnostic("debug", "api", "Fetch candidate", { index, url });
        response = await sendHttpRequest(url, init);
        logDiagnostic("debug", "api", "Fetch candidate returned", {
          index,
          url,
          status: response.status,
          ok: response.ok,
        });
        break;
      } catch (error) {
        logDiagnostic("warn", "api", "Fetch candidate failed", { index, url, error });
        if (error instanceof DOMException && error.name === "AbortError") {
          throw error;
        }
        if (index === urls.length - 1) {
          throw new TypeError(error instanceof Error ? error.message : "Network request failed.");
        }
      }
    }
    if (response === undefined) {
      throw new TypeError("Network request failed.");
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      logDiagnostic("warn", "api", "Request aborted", { path });
      throw error;
    }
    logDiagnostic("error", "api", "Request network failure", { path, error });
    throw new ApiError("Unable to reach the server.", 0, "NETWORK_ERROR", null);
  }

  const requestId = response.headers.get("x-request-id");
  const payload = await parseJson(response);
  if (!response.ok) {
    logDiagnostic("warn", "api", "Request failed response", {
      method: options.method ?? "GET",
      path,
      status: response.status,
      requestId,
      elapsedMs: Math.round(performance.now() - startedAt),
    });
    throw toApiError(payload, response.status, requestId);
  }
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(API_OK_EVENT));
  }
  logDiagnostic("info", "api", "Request success", {
    method: options.method ?? "GET",
    path,
    status: response.status,
    requestId,
    elapsedMs: Math.round(performance.now() - startedAt),
  });
  return payload as T;
}

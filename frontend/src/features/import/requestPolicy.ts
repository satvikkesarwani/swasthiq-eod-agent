import { BACKEND_REQUEST_LIMIT_BYTES } from "./constants";
import { stringifySafeJson } from "./jsonSafety";

export function estimateBillingRequestBytes(payload: unknown): number {
  return new TextEncoder().encode(stringifySafeJson(payload)).byteLength;
}

export function isEstimatedRequestTooLarge(payload: unknown): boolean {
  return estimateBillingRequestBytes(payload) > BACKEND_REQUEST_LIMIT_BYTES;
}

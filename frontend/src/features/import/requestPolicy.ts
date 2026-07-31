import { BACKEND_REQUEST_LIMIT_BYTES } from "./constants";

export function estimateBillingRequestBytes(payload: unknown): number {
  return new TextEncoder().encode(JSON.stringify(payload)).byteLength;
}

export function isEstimatedRequestTooLarge(payload: unknown): boolean {
  return estimateBillingRequestBytes(payload) > BACKEND_REQUEST_LIMIT_BYTES;
}

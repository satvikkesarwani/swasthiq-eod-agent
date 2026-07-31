import { ApiError } from "../../api/client";

export type SafeMappedError = {
  code: string;
  message: string;
  requestId: string | null;
  details: unknown[];
};

export function mapImportError(error: unknown): SafeMappedError | null {
  if (error instanceof DOMException && error.name === "AbortError") {
    return null;
  }
  if (error instanceof ApiError) {
    if (error.status === 413 || error.code === "REQUEST_TOO_LARGE") {
      return { code: error.code, message: "The selected request exceeds the billing service limit.", requestId: error.requestId, details: error.details };
    }
    if (error.code === "NO_VALID_RECORDS") {
      return { code: error.code, message: "No valid rows were found. No report was stored or replaced.", requestId: error.requestId, details: error.details };
    }
    if (error.status === 422 || error.code === "VALIDATION_ERROR") {
      return { code: error.code, message: "The billing request did not pass service validation.", requestId: error.requestId, details: error.details };
    }
    if (error.status === 409) {
      return { code: error.code, message: "The billing service reported a conflict. Refresh reports and retry.", requestId: error.requestId, details: error.details };
    }
    if (error.status === 0 || error.code === "NETWORK_ERROR") {
      return { code: error.code, message: "The billing service could not be reached.", requestId: error.requestId, details: error.details };
    }
    if (error.code === "MALFORMED_JSON") {
      return { code: error.code, message: "The billing service returned a malformed response.", requestId: error.requestId, details: error.details };
    }
    return { code: error.code, message: "The billing service could not complete the request.", requestId: error.requestId, details: error.details };
  }
  return { code: "UNKNOWN_ERROR", message: "The billing service could not complete the request.", requestId: null, details: [] };
}

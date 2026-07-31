import { describe, expect, it } from "vitest";

import { ApiError } from "../../api/client";
import { mapImportError } from "./errorMapping";
import { estimateBillingRequestBytes, isEstimatedRequestTooLarge } from "./requestPolicy";
import { BACKEND_REQUEST_LIMIT_BYTES } from "./constants";

describe("import error mapping and request policy", () => {
  it("maps known backend and network errors safely", () => {
    expect(mapImportError(new ApiError("too large", 413, "REQUEST_TOO_LARGE", "req-1"))).toMatchObject({ message: "The selected request exceeds the billing service limit.", requestId: "req-1" });
    expect(mapImportError(new ApiError("none", 422, "NO_VALID_RECORDS", null))).toMatchObject({ message: "No valid rows were found. No report was stored or replaced." });
    expect(mapImportError(new ApiError("bad", 422, "VALIDATION_ERROR", null))).toMatchObject({ message: "The billing request did not pass service validation." });
    expect(mapImportError(new ApiError("conflict", 409, "CONFLICT", null))).toMatchObject({ message: "The billing service reported a conflict. Refresh reports and retry." });
    expect(mapImportError(new ApiError("offline", 0, "NETWORK_ERROR", null))).toMatchObject({ message: "The billing service could not be reached." });
    expect(mapImportError(new ApiError("malformed", 200, "MALFORMED_JSON", null))).toMatchObject({ message: "The billing service returned a malformed response." });
    expect(mapImportError(new Error("boom"))).toMatchObject({ code: "UNKNOWN_ERROR" });
    expect(mapImportError(new DOMException("aborted", "AbortError"))).toBeNull();
  });

  it("estimates serialized request size", () => {
    expect(estimateBillingRequestBytes({ records: [] })).toBeGreaterThan(0);
    expect(isEstimatedRequestTooLarge({ records: ["x".repeat(BACKEND_REQUEST_LIMIT_BYTES)] })).toBe(true);
  });
});

import { describe, expect, it } from "vitest";

import { MAX_BILLING_FILE_BYTES } from "./constants";
import { isValidBusinessDateInput, normalizeBusinessDateInput, trimOptional, validateBillingFile, validateDroppedFiles } from "./validation";

function sizedFile(size: number, name = "billing.json", type = "application/json") {
  return new File([new Uint8Array(size)], name, { type });
}

describe("import validation", () => {
  it("accepts JSON extension variants and rejects unsupported files", () => {
    expect(validateBillingFile(sizedFile(2, "BILLING.JSON", ""))).toBeNull();
    expect(validateBillingFile(sizedFile(2, "billing.json", "text/plain"))).toBeNull();
    expect(validateBillingFile(sizedFile(2, "billing.txt"))).toMatchObject({ code: "UNSUPPORTED_FILE" });
  });

  it("enforces size and drop count policies", () => {
    expect(validateBillingFile(sizedFile(MAX_BILLING_FILE_BYTES))).toBeNull();
    expect(validateBillingFile(sizedFile(MAX_BILLING_FILE_BYTES + 1))).toMatchObject({ code: "FILE_TOO_LARGE" });
    expect(validateDroppedFiles([])).toMatchObject({ code: "NO_FILE" });
    expect(validateDroppedFiles([sizedFile(1), sizedFile(1)])).toMatchObject({ code: "MULTIPLE_FILES" });
  });

  it("validates date strings and trims optional metadata", () => {
    expect(isValidBusinessDateInput("2026-07-31")).toBe(true);
    expect(isValidBusinessDateInput("31/07/2026")).toBe(true);
    expect(isValidBusinessDateInput("2026-02-30")).toBe(false);
    expect(isValidBusinessDateInput("31/02/2026")).toBe(false);
    expect(normalizeBusinessDateInput("31/07/2026")).toBe("2026-07-31");
    expect(normalizeBusinessDateInput("2026-07-31")).toBe("2026-07-31");
    expect(normalizeBusinessDateInput("07/31/2026")).toBeNull();
    expect(trimOptional("  Kanpur  ")).toBe("Kanpur");
    expect(trimOptional("   ")).toBeUndefined();
  });
});

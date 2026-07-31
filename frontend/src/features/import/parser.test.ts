import { describe, expect, it, vi } from "vitest";

import { validSalesRecords } from "../../test/fixtures";
import { BillingFileParseError, parseBillingLogFile } from "./parser";

function jsonFile(body: string, name = "billing.json", type = "application/json") {
  return new File([body], name, { type });
}

describe("parseBillingLogFile", () => {
  it("parses valid arrays, empty arrays, BOM files and preserves order", async () => {
    const parsed = await parseBillingLogFile(jsonFile(JSON.stringify([1, { a: 2 }, "bad"])));
    expect(parsed.records).toEqual([1, { a: 2 }, "bad"]);
    expect(parsed.rowCount).toBe(3);
    expect(parsed.isEmpty).toBe(false);
    await expect(parseBillingLogFile(jsonFile("[]", "empty.JSON", ""))).resolves.toMatchObject({ rowCount: 0, isEmpty: true });
    await expect(parseBillingLogFile(jsonFile(`\uFEFF${JSON.stringify(validSalesRecords)}`))).resolves.toMatchObject({ rowCount: 1 });
  });

  it("rejects invalid JSON and non-array roots safely", async () => {
    await expect(parseBillingLogFile(jsonFile("{"))).rejects.toMatchObject({ code: "INVALID_JSON" });
    await expect(parseBillingLogFile(jsonFile('[{"a":1,"a":2}]'))).rejects.toMatchObject({ code: "INVALID_JSON" });
    await expect(parseBillingLogFile(jsonFile(`[{"amount_paid_paise":${Number.MAX_SAFE_INTEGER + 1}}]`))).rejects.toMatchObject({ code: "INVALID_JSON" });
    await expect(parseBillingLogFile(jsonFile("{}"))).rejects.toMatchObject({ code: "ROOT_NOT_ARRAY" });
    await expect(parseBillingLogFile(jsonFile("\"x\""))).rejects.toMatchObject({ code: "ROOT_NOT_ARRAY" });
    await expect(parseBillingLogFile(jsonFile("null"))).rejects.toMatchObject({ code: "ROOT_NOT_ARRAY" });
  });

  it("handles empty text and file read failures", async () => {
    await expect(parseBillingLogFile(jsonFile(""))).rejects.toBeInstanceOf(BillingFileParseError);
    await expect(parseBillingLogFile(new File([new Uint8Array([0xff])], "billing.json", { type: "application/json" }))).rejects.toMatchObject({ code: "FILE_READ_FAILED" });
    const file = { name: "billing.json", size: 2, arrayBuffer: vi.fn().mockRejectedValue(new Error("blocked")) } as unknown as File;
    await expect(parseBillingLogFile(file)).rejects.toMatchObject({ code: "FILE_READ_FAILED" });
  });
});

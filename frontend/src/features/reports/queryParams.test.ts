import { describe, expect, it } from "vitest";

import { parseReportsQuery, reportsQueryToSearch } from "./queryParams";

describe("report query params", () => {
  it("parses and serializes filters and pagination", () => {
    const query = parseReportsQuery("?clinic_id=CLN&date_from=2026-07-01&date_to=2026-07-31&offset=10&limit=10");
    expect(query).toMatchObject({ clinicId: "CLN", dateFrom: "2026-07-01", dateTo: "2026-07-31", offset: 10, rangeError: null });
    expect(reportsQueryToSearch(query)).toContain("clinic_id=CLN");
  });

  it("detects invalid date ranges and omits empty values", () => {
    const query = parseReportsQuery("?clinic_id=&date_from=2026-08-01&date_to=2026-07-01&offset=-1");
    expect(query.rangeError).toBe("Date from cannot be after date to.");
    expect(query.offset).toBe(0);
    expect(reportsQueryToSearch({ limit: 10, offset: 0, rangeError: null })).toBe("");
  });
});

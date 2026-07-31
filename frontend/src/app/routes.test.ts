import { describe, expect, it } from "vitest";

import { analyticsPath, hasValidReportParams, isValidBusinessDate, reconciliationPath } from "./routes";

describe("route helpers", () => {
  it("builds encoded report detail links", () => {
    expect(reconciliationPath("clinic 1", "2026-07-31")).toBe("/reports/clinic%201/2026-07-31/reconciliation");
    expect(analyticsPath("clinic/a", "2026-07-31")).toBe("/reports/clinic%2Fa/2026-07-31/analytics");
  });

  it("validates report params strictly", () => {
    expect(isValidBusinessDate("2026-07-31")).toBe(true);
    expect(isValidBusinessDate("2026-02-30")).toBe(false);
    expect(hasValidReportParams({ clinicId: "clinic-a", businessDate: "2026-07-31" })).toBe(true);
    expect(hasValidReportParams({ clinicId: "", businessDate: "2026-07-31" })).toBe(false);
  });
});

import { describe, expect, it } from "vitest";

import {
  formatBusinessDate,
  formatCount,
  formatFileSize,
  formatPaise,
  formatPercentage,
  formatUtcHourRange,
  safeLabel,
} from "./formatters";

describe("formatters", () => {
  it("formats deterministic currency without floating point drift", () => {
    expect(formatPaise(123456789)).toBe("₹12,34,567.89");
    expect(formatPaise(-500)).toBe("-₹5");
    expect(formatPaise(Number.NaN)).toBe("₹0");
  });

  it("formats counts, dates, hours, percentages and file sizes", () => {
    expect(formatCount(12345.9)).toBe("12,345");
    expect(formatBusinessDate("2026-07-31")).toContain("2026");
    expect(formatBusinessDate("bad-date")).toBe("Date unavailable");
    expect(formatUtcHourRange(9, 17)).toBe("09:00-17:00 UTC");
    expect(formatUtcHourRange(-1, 17)).toBe("Hour unavailable");
    expect(formatPercentage(0.923)).toBe("92.3%");
    expect(formatPercentage(undefined)).toBe("Not available");
    expect(formatFileSize(1536)).toBe("1.5 KB");
    expect(formatFileSize(0)).toBe("0 B");
    expect(safeLabel(" Clinic A ")).toBe("Clinic A");
    expect(safeLabel("")).toBe("Unavailable");
  });
});

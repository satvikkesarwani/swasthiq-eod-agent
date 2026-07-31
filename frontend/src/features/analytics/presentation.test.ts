import { describe, expect, it } from "vitest";

import { analyticsReport, emptyDayReport, partialAnalyticsReport, refundOnlyReport } from "../../test/fixtures";
import { formatUtcHourRange, getAnalyticsContext, mapHourlyRevenue, peakPresentation, quantityUnit, shortHash, validateAnalyticsContract } from "./presentation";

describe("analytics presentation mapping", () => {
  it("maps hourly revenue in backend order and marks only backend peak hour", () => {
    const points = mapHourlyRevenue(analyticsReport);

    expect(points.map((point) => point.hourKey)).toEqual(["10", "9", "11"]);
    expect(points.map((point) => point.revenuePaise)).toEqual([90000, 50000, 70000]);
    expect(points.map((point) => point.isPeak)).toEqual([false, true, false]);
    expect(peakPresentation(analyticsReport)).toMatchObject({ hour: "09:00-10:00 UTC", amount: "₹500" });
  });

  it("uses backend ranking order without resorting by displayed values", () => {
    expect(analyticsReport.report.analytics.top_medicines_by_quantity.map((item) => `${item.rank}:${item.drug_name}:${item.quantity}`)).toEqual([
      "1:ORS:5",
      "2:Paracetamol:20",
      "3:Cough Syrup:10",
    ]);
    expect(analyticsReport.report.analytics.top_medicines_by_revenue.map((item) => `${item.rank}:${item.drug_name}:${item.revenue_paise}`)).toEqual([
      "1:Vitamin D:10000",
      "2:Antibiotic Course:50000",
    ]);
  });

  it("describes partial, empty, refund-only and sales contexts", () => {
    expect(getAnalyticsContext(partialAnalyticsReport).kind).toBe("partial");
    expect(getAnalyticsContext(emptyDayReport).kind).toBe("empty");
    expect(getAnalyticsContext(refundOnlyReport).kind).toBe("refund_only");
    expect(getAnalyticsContext(analyticsReport).kind).toBe("sales_and_refunds");
  });

  it("validates malformed analytics contracts and formats helper labels", () => {
    expect(validateAnalyticsContract(analyticsReport)).toBeNull();
    expect(formatUtcHourRange(23, 24)).toBe("23:00-24:00 UTC");
    expect(quantityUnit(1)).toBe("1 unit");
    expect(quantityUnit(20)).toBe("20 units");
    expect(shortHash("sha256:report-detail-abcdef")).toBe("sha256:repor");
    expect(validateAnalyticsContract({
      ...analyticsReport,
      report: {
        ...analyticsReport.report,
        analytics: {
          ...analyticsReport.report.analytics,
          revenue_by_hour: [{ hour_utc: 99, revenue_paise: 10 }],
        },
      },
    })).toBe("The analytics response could not be verified.");
  });
});

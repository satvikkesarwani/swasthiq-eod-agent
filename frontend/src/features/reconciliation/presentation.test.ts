import { describe, expect, it } from "vitest";

import { emptyDayReport, makeClinicDayReport, partialReconciliationReport, refundOnlyReport } from "../../test/fixtures";
import {
  collectionRateVisualPercent,
  formatCollectionRate,
  getCollectionHealth,
  getDayActivity,
  importNotice,
  mapMetrics,
  orderPaymentModes,
  reportHashPrefix,
  validateReportParams,
} from "./presentation";

describe("reconciliation presentation mapping", () => {
  it("preserves backend metric values without arithmetic", () => {
    const report = makeClinicDayReport({
      report: {
        ...makeClinicDayReport().report,
        reconciliation: {
          ...makeClinicDayReport().report.reconciliation,
          total_billed_paise: 10000,
          total_collected_paise: 9000,
          total_outstanding_paise: 777,
          collection_rate: 0.42,
        },
      },
    });

    expect(mapMetrics(report).map((metric) => metric.valuePaise)).toEqual([10000, 9000, 777, 1050]);
    expect(formatCollectionRate(report.report.reconciliation.collection_rate)).toBe("42.0%");
  });

  it("maps fully collected, outstanding, no-sales, refund-only and partial states", () => {
    expect(getCollectionHealth(makeClinicDayReport({ report: { ...makeClinicDayReport().report, reconciliation: { ...makeClinicDayReport().report.reconciliation, total_outstanding_paise: 0 } } })).label).toBe("Fully collected");
    expect(getCollectionHealth(makeClinicDayReport()).label).toBe("Collection pending");
    expect(getCollectionHealth(emptyDayReport).label).toBe("No sales collection required");
    expect(getCollectionHealth(refundOnlyReport).label).toBe("Refund activity only");
    expect(getDayActivity(partialReconciliationReport).kind).toBe("partial");
  });

  it("orders known payment modes and keeps unknown backend rows without synthesizing totals", () => {
    const report = makeClinicDayReport({
      report: {
        ...makeClinicDayReport().report,
        reconciliation: {
          ...makeClinicDayReport().report.reconciliation,
          by_payment_mode: {
            upi: { billed_paise: 1, collected_paise: 2, outstanding_paise: 3, refunds_paise: 4 },
            wallet: { billed_paise: 5, collected_paise: 6, outstanding_paise: 7, refunds_paise: 8 },
            cash: { billed_paise: 9, collected_paise: 10, outstanding_paise: 11, refunds_paise: 12 },
          },
        },
      },
    });

    expect(orderPaymentModes(report).map((row) => row.mode)).toEqual(["cash", "upi", "wallet"]);
    expect(orderPaymentModes(report).find((row) => row.mode === "cash")?.metrics.billed_paise).toBe(9);
  });

  it("handles collection rate null and visual clamping without changing displayed text", () => {
    expect(formatCollectionRate(null)).toBe("Not applicable");
    expect(formatCollectionRate(1.23456)).toBe("123.5%");
    expect(collectionRateVisualPercent(1.23456)).toBe(100);
    expect(collectionRateVisualPercent(-0.5)).toBe(0);
  });

  it("validates route params and safe metadata helpers", () => {
    expect(validateReportParams({ clinicId: " CLN ", businessDate: "2026-07-31" })).toEqual({ clinicId: "CLN", businessDate: "2026-07-31" });
    expect(validateReportParams({ clinicId: "", businessDate: "2026-07-31" })).toBeNull();
    expect(reportHashPrefix("sha256:abcdef1234567890")).toBe("sha256:abcde");
    expect(importNotice("created")).toBe("Clinic-day report created successfully.");
    expect(importNotice("unknown")).toBeNull();
  });
});

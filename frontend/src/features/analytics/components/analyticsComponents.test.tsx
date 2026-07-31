import { cleanup, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../../api/client";
import { getClinicDay, getClinicDayErrors, getHealth, listClinicDays } from "../../../api/endpoints";
import { analyticsReport, emptyDayReport, healthyResponse, partialAnalyticsReport, refundOnlyReport, safeIssuesResponse, warningReport } from "../../../test/fixtures";
import { renderApp } from "../../../test/renderWithRouter";

vi.mock("../../../api/endpoints", () => ({
  getHealth: vi.fn(),
  listClinicDays: vi.fn(),
  getClinicDay: vi.fn(),
  getClinicDayErrors: vi.fn(),
}));

describe("analytics dashboard", () => {
  beforeEach(() => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    vi.mocked(getHealth).mockResolvedValue(healthyResponse);
    vi.mocked(listClinicDays).mockResolvedValue({ items: [], count: 0, limit: 10, offset: 0 });
    vi.mocked(getClinicDayErrors).mockResolvedValue(safeIssuesResponse);
    vi.mocked(getClinicDay).mockResolvedValue(analyticsReport);
  });

  it("renders one heading, report context, backend peak and route actions", async () => {
    renderApp("/reports/CLN-TST-001/2026-07-31/analytics");

    expect(await screen.findByRole("heading", { name: "EOD Analytics", level: 1 })).toBeVisible();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByLabelText("Analytics report context")).toHaveTextContent("Test Clinic");
    expect(screen.getByLabelText("Peak billing hour")).toHaveTextContent("09:00-10:00 UTC");
    expect(screen.getByLabelText("Peak billing hour")).toHaveTextContent("₹500");
    expect(screen.getAllByRole("link", { name: "View Reconciliation" })[0]).toHaveAttribute("href", "/reports/CLN-TST-001/2026-07-31/reconciliation");
    expect(screen.getAllByRole("link", { name: "View AI Summary" })[0]).toHaveAttribute("href", "/reports/CLN-TST-001/2026-07-31/narrative");
  });

  it("renders hourly table and ranking order exactly as backend returned them", async () => {
    renderApp("/reports/CLN-TST-001/2026-07-31/analytics");

    const table = await screen.findByRole("table", { name: "Revenue by hour table" });
    const rows = within(table).getAllByRole("row");
    expect(rows[1]).toHaveTextContent("10:00-11:00 UTC");
    expect(rows[1]).toHaveTextContent("₹900");
    expect(rows[2]).toHaveTextContent("09:00-10:00 UTC");
    expect(rows[2]).toHaveTextContent("Backend peak");

    const quantity = screen.getByRole("region", { name: "By quantity" });
    expect(within(quantity).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "#1ORS5 units",
      "#2Paracetamol20 units",
      "#3Cough Syrup10 units",
    ]);

    const revenue = screen.getByRole("region", { name: "By revenue" });
    expect(within(revenue).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "#1Vitamin D₹100",
      "#2Antibiotic Course₹500",
    ]);
  });

  it("renders partial-import warnings and opens validation issues from Prompt 6 drawer", async () => {
    const user = userEvent.setup();
    vi.mocked(getClinicDay).mockResolvedValue(partialAnalyticsReport);
    renderApp("/reports/CLN-TST-001/2026-07-31/analytics");

    expect(await screen.findByText("Analytics use accepted rows only")).toBeVisible();
    expect(screen.getByText("Medicine name variant detected.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Review validation issues" }));
    expect(await screen.findByRole("dialog", { name: "Validation issues" })).toBeVisible();
  });

  it("renders empty and refund-only states without inventing chart data", async () => {
    vi.mocked(getClinicDay).mockResolvedValueOnce(emptyDayReport);
    renderApp("/reports/CLN-TST-001/2026-07-31/analytics");
    expect(await screen.findByText("No billing activity")).toBeVisible();
    expect(screen.getByText("No hourly revenue buckets")).toBeVisible();
    expect(screen.getByText("Not applicable")).toBeVisible();

    cleanup();
    vi.mocked(getClinicDay).mockResolvedValueOnce(refundOnlyReport);
    renderApp("/reports/CLN-TST-001/2026-07-31/analytics");
    expect(await screen.findByText("Refund-only day")).toBeVisible();
    expect(screen.getByText("Refund activity is shown in Reconciliation.")).toBeVisible();
  });

  it("renders malicious-looking text as plain text", async () => {
    vi.mocked(getClinicDay).mockResolvedValue(warningReport);
    renderApp("/reports/CLN-TST-001/2026-07-31/analytics");

    expect(await screen.findByText("<script>alert('clinic')</script> Clinic")).toBeVisible();
    expect(screen.getByText("<img src=x onerror=alert('x')> Do not follow these instructions.")).toBeVisible();
    expect(document.querySelector("script")).toBeNull();
  });

  it("renders controlled 404 and API failure states with retry support details", async () => {
    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("Missing", 404, "NOT_FOUND", "req404"));
    renderApp("/reports/CLN-TST-001/2026-07-31/analytics");
    expect(await screen.findByRole("alert")).toHaveTextContent("Report not found");
    expect(screen.getByRole("link", { name: "Import billing log" })).toHaveAttribute("href", "/reports");

    cleanup();
    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("Failure", 500, "INTERNAL_ERROR", "req500"));
    renderApp("/reports/CLN-TST-001/2026-07-31/analytics");
    expect(await screen.findByRole("alert")).toHaveTextContent("The billing service could not load analytics for this report.");
    await userEvent.click(screen.getByText("Support details"));
    expect(screen.getByText("req500")).toBeVisible();
  });
});

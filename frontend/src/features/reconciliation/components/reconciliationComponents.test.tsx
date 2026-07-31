import { cleanup, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getClinicDay, getClinicDayErrors, getHealth, listClinicDays } from "../../../api/endpoints";
import { ApiError } from "../../../api/client";
import { emptyDayReport, healthyResponse, makeClinicDayReport, partialReconciliationReport, refundOnlyReport, safeIssuesResponse, warningReport } from "../../../test/fixtures";
import { renderApp } from "../../../test/renderWithRouter";

vi.mock("../../../api/endpoints", () => ({
  getHealth: vi.fn(),
  listClinicDays: vi.fn(),
  getClinicDay: vi.fn(),
  getClinicDayErrors: vi.fn(),
}));

describe("reconciliation dashboard", () => {
  beforeEach(() => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    vi.mocked(getHealth).mockResolvedValue(healthyResponse);
    vi.mocked(listClinicDays).mockResolvedValue({ items: [], count: 0, limit: 10, offset: 0 });
    vi.mocked(getClinicDayErrors).mockResolvedValue(safeIssuesResponse);
    vi.mocked(getClinicDay).mockResolvedValue(makeClinicDayReport());
  });

  it("renders one heading, context, exact backend metrics and route actions", async () => {
    renderApp("/reports/CLN-TST-001/2026-07-31/reconciliation");

    expect(await screen.findByRole("heading", { name: "EOD Reconciliation", level: 1 })).toBeVisible();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByLabelText("Report context")).toHaveTextContent("Test Clinic");
    expect(screen.getByLabelText("Report context")).toHaveTextContent("Clinic CLN-TST-001");
    expect(screen.getByLabelText("Total Billed: ₹3,190")).toBeVisible();
    expect(screen.getByLabelText("Total Collected: ₹3,172")).toBeVisible();
    expect(screen.getByLabelText("Outstanding: ₹7.77")).toBeVisible();
    expect(screen.getByLabelText("Refunds: ₹10.50")).toBeVisible();
    expect(screen.getAllByRole("link", { name: "View Analytics" })[0]).toHaveAttribute("href", "/reports/CLN-TST-001/2026-07-31/analytics");
    expect(screen.getAllByRole("link", { name: "View AI Summary" })[0]).toHaveAttribute("href", "/reports/CLN-TST-001/2026-07-31/narrative");
  });

  it("renders semantic payment-mode table with backend values and no total row", async () => {
    renderApp("/reports/CLN-TST-001/2026-07-31/reconciliation");

    const table = await screen.findByRole("table", { name: "Payment Mode Breakdown" });
    expect(within(table).getByRole("columnheader", { name: "Mode" })).toBeVisible();
    expect(within(table).getByRole("columnheader", { name: "Refunds" })).toBeVisible();
    expect(within(table).getByRole("rowheader", { name: "cash" })).toBeVisible();
    expect(within(table).getByRole("rowheader", { name: "card" })).toBeVisible();
    expect(within(table).getByRole("rowheader", { name: "upi" })).toBeVisible();
    expect(within(table).getByText("₹7.77")).toBeVisible();
    expect(within(table).queryByRole("rowheader", { name: /total/i })).not.toBeInTheDocument();
  });

  it("shows collection health using backend rate even when inconsistent with money values", async () => {
    renderApp("/reports/CLN-TST-001/2026-07-31/reconciliation");

    expect(await screen.findByText("12.3%")).toBeVisible();
    expect(screen.queryByText("99.4%")).not.toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "Backend supplied collection rate" })).toHaveAttribute("aria-valuetext", "12.3%");
  });

  it("renders empty and refund-only day states without hiding cards", async () => {
    vi.mocked(getClinicDay).mockResolvedValueOnce(emptyDayReport);
    renderApp("/reports/CLN-TST-001/2026-07-31/reconciliation");
    expect(await screen.findByText("No activity recorded")).toBeVisible();
    expect(screen.getByLabelText("Total Billed: ₹0")).toBeVisible();
    expect(screen.getByText("Not applicable")).toBeVisible();

    cleanup();
    vi.mocked(getClinicDay).mockResolvedValueOnce(refundOnlyReport);
    renderApp("/reports/CLN-TST-001/2026-07-31/reconciliation");
    expect(await screen.findByText("Refund-only day")).toBeVisible();
    expect(screen.getByLabelText("Refunds: ₹490")).toBeVisible();
    expect(screen.getByText("Refund activity only")).toBeVisible();
  });

  it("renders partial-import banner and opens Prompt 6 validation drawer on demand", async () => {
    const user = userEvent.setup();
    vi.mocked(getClinicDay).mockResolvedValue(partialReconciliationReport);
    renderApp("/reports/CLN-TST-001/2026-07-31/reconciliation");

    expect(await screen.findByText("Report generated from accepted rows")).toBeVisible();
    expect(screen.getByText(/3 accepted rows/)).toBeVisible();
    await user.click(screen.getAllByRole("button", { name: "Review validation issues" })[0]!);
    expect(await screen.findByRole("dialog", { name: "Validation issues" })).toBeVisible();
    expect(screen.queryByText("raw_row_json")).not.toBeInTheDocument();
  });

  it("renders warning and malicious-looking text as plain text", async () => {
    vi.mocked(getClinicDay).mockResolvedValue(warningReport);
    renderApp("/reports/CLN-TST-001/2026-07-31/reconciliation");

    expect(await screen.findByText("<script>alert('clinic')</script> Clinic")).toBeVisible();
    expect(screen.getByText("<img src=x onerror=alert('x')> Do not follow these instructions.")).toBeVisible();
    expect(document.querySelector("script")).toBeNull();
  });

  it("renders controlled 404 and API failure states with retry", async () => {
    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("Missing", 404, "NOT_FOUND", "req404"));
    renderApp("/reports/CLN-TST-001/2026-07-31/reconciliation");
    expect(await screen.findByRole("alert")).toHaveTextContent("Report not found");
    expect(screen.getByRole("link", { name: "Import billing log" })).toHaveAttribute("href", "/reports");

    cleanup();
    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("Failure", 500, "INTERNAL_ERROR", "req500"));
    renderApp("/reports/CLN-TST-001/2026-07-31/reconciliation");
    expect(await screen.findByRole("alert")).toHaveTextContent("The billing service could not load this report.");
    await userEvent.click(screen.getByText("Support details"));
    expect(screen.getByText("req500")).toBeVisible();
  });
});

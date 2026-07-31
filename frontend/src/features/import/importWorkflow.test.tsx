import { screen, waitFor } from "@testing-library/dom";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AppProviders } from "../../app/AppProviders";
import { AppShell } from "../../components/layout/AppShell";
import { ReportsHomePage } from "../../pages/ReportsHomePage";
import { createdImportResponse, partialImportResponse, recentReportsResponse, safeIssuesResponse, validSalesRecords } from "../../test/fixtures";
import { reportsLoader } from "../reports/loader";

vi.mock("../../api/endpoints", () => ({
  getHealth: vi.fn().mockResolvedValue({ status: "ok", version: "test", database: "ok" }),
  listClinicDays: vi.fn(),
  putClinicDay: vi.fn(),
  getClinicDayErrors: vi.fn(),
}));

function renderReports() {
  const router = createMemoryRouter([
    {
      path: "/",
      Component: AppProviders,
      children: [
        {
          Component: AppShell,
          children: [{ path: "reports", Component: ReportsHomePage, loader: reportsLoader }],
        },
      ],
    },
  ], { initialEntries: ["/reports"] });
  return { router, ...render(<RouterProvider router={router} />) };
}

describe("billing import workflow", () => {
  beforeEach(async () => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    const { listClinicDays, putClinicDay, getClinicDayErrors } = await import("../../api/endpoints");
    vi.mocked(listClinicDays).mockResolvedValue(recentReportsResponse);
    vi.mocked(putClinicDay).mockResolvedValue(partialImportResponse);
    vi.mocked(getClinicDayErrors).mockResolvedValue(safeIssuesResponse);
  });

  it("submits parsed records unchanged and opens safe partial-import issues", async () => {
    renderReports();
    await screen.findByRole("heading", { name: "Reports" });

    const clinicInput = screen.getAllByLabelText("Clinic ID")[0];
    const dateInput = screen.getAllByLabelText("Business date")[0];
    expect(clinicInput).toBeDefined();
    expect(dateInput).toBeDefined();
    await userEvent.type(clinicInput as HTMLElement, " CLN-TST-001 ");
    await userEvent.type(dateInput as HTMLElement, "31/07/2026");
    await userEvent.click(screen.getByLabelText("I understand this may replace the stored report for this clinic day."));
    const file = new File([JSON.stringify([{ ok: true }, "bad row"])], "billing.json", { type: "" });
    await userEvent.upload(screen.getByLabelText("Billing log JSON file"), file);
    await waitFor(() => expect(screen.getByText("billing.json")).toBeVisible());

    await userEvent.click(screen.getByRole("button", { name: "Replace report" }));
    const { putClinicDay } = await import("../../api/endpoints");
    await waitFor(() => expect(putClinicDay).toHaveBeenCalledTimes(1));
    expect(vi.mocked(putClinicDay).mock.calls[0]?.[0]).toBe("CLN-TST-001");
    expect(vi.mocked(putClinicDay).mock.calls[0]?.[1]).toBe("2026-07-31");
    expect(vi.mocked(putClinicDay).mock.calls[0]?.[2]).toMatchObject({ records: [{ ok: true }, "bad row"] });

    expect(await screen.findByText("Report generated with validation issues")).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Review issues" }));
    expect(await screen.findByRole("dialog", { name: "Validation issues" })).toBeVisible();
    expect(screen.getByText("Line items are invalid.")).toBeVisible();
    expect(screen.queryByText("raw_row_json")).not.toBeInTheDocument();
  });

  it("shows accessible validation errors and unsupported-file errors", async () => {
    renderReports();
    await screen.findByRole("heading", { name: "Reports" });

    await userEvent.click(screen.getByRole("button", { name: "Validate and generate report" }));
    expect(screen.getByText("Clinic ID is required.")).toBeVisible();
    expect(screen.getByText("Business date is required as DD/MM/YYYY or YYYY-MM-DD.")).toBeVisible();
    expect(screen.getByText("Choose a JSON billing log.")).toBeVisible();

    const badFile = new File(["[]"], "billing.txt", { type: "text/plain" });
    await userEvent.upload(screen.getByLabelText("Billing log JSON file"), badFile, { applyAccept: false });
    expect(await screen.findByText("Choose a JSON file with the .json extension.")).toBeVisible();
  });

  it("navigates after a full successful new report import", async () => {
    const { listClinicDays, putClinicDay } = await import("../../api/endpoints");
    vi.mocked(listClinicDays).mockResolvedValue({ count: 0, items: [], limit: 10, offset: 0 });
    vi.mocked(putClinicDay).mockResolvedValue(createdImportResponse);
    const { router } = renderReports();
    await screen.findByRole("heading", { name: "Reports" });

    const clinicInput = screen.getAllByLabelText("Clinic ID")[0];
    const dateInput = screen.getAllByLabelText("Business date")[0];
    expect(clinicInput).toBeDefined();
    expect(dateInput).toBeDefined();
    await userEvent.type(clinicInput as HTMLElement, "CLN-TST-001");
    await userEvent.type(dateInput as HTMLElement, "2026-07-31");
    await userEvent.upload(screen.getByLabelText("Billing log JSON file"), new File([JSON.stringify(validSalesRecords)], "billing.json", { type: "application/json" }));
    await screen.findByText("billing.json");
    await userEvent.click(screen.getByRole("button", { name: "Validate and generate report" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/reports/CLN-TST-001/2026-07-31/reconciliation"));
  });
});

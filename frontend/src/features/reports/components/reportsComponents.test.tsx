import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";

import { recentReportsResponse } from "../../../test/fixtures";
import { RECENT_REPORTS_LIMIT } from "../queryParams";
import { RecentReportsFilters } from "./RecentReportsFilters";
import { RecentReportsList } from "./RecentReportsList";
import { RecentReportsPanel } from "./RecentReportsPanel";
import { ReportsPagination } from "./ReportsPagination";

function renderRouter(element: React.ReactNode, path = "/reports") {
  const router = createMemoryRouter([{ path: "/reports", element }], { initialEntries: [path] });
  return { router, ...render(<RouterProvider router={router} />) };
}

describe("recent reports components", () => {
  it("renders backend-provided report values and encoded links", () => {
    renderRouter(<RecentReportsList reports={recentReportsResponse.items} />);
    expect(screen.getByText("Test Clinic")).toBeVisible();
    expect(screen.getAllByText("₹10")).toHaveLength(2);
    expect(screen.getByRole("link", { name: "Open report" })).toHaveAttribute("href", "/reports/CLN-TST-001/2026-07-31/reconciliation");
  });

  it("renders rejected-row badges from backend values", () => {
    const [report] = recentReportsResponse.items;
    expect(report).toBeDefined();
    renderRouter(<RecentReportsList reports={[{ ...report!, rejected_rows: 2, status: "completed_with_errors" }]} />);
    expect(screen.getByText("2 rejected")).toBeVisible();
    expect(screen.getByText("completed_with_errors")).toBeVisible();
  });

  it("applies and resets URL filters", async () => {
    const { router } = renderRouter(<RecentReportsFilters query={{ limit: RECENT_REPORTS_LIMIT, offset: 0, rangeError: null }} />);
    await userEvent.type(screen.getByLabelText("Clinic ID"), "CLN");
    await userEvent.type(screen.getByLabelText("Date from"), "2026-07-01");
    await userEvent.click(screen.getByRole("button", { name: "Apply filters" }));
    expect(router.state.location.search).toContain("clinic_id=CLN");
    await userEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(router.state.location.search).toBe("");
  });

  it("renders empty, error and pagination states", async () => {
    const query = { limit: 10, offset: 0, rangeError: null };
    const { rerender, router } = renderRouter(<RecentReportsPanel data={{ query, response: { count: 0, items: [], limit: 10, offset: 0 }, error: null }} />);
    expect(screen.getByText("No clinic-day reports yet")).toBeVisible();
    rerender(<RouterProvider router={createMemoryRouter([{ path: "/reports", element: <RecentReportsPanel data={{ query, response: null, error: "Bad range" }} /> }], { initialEntries: ["/reports"] })} />);
    expect(screen.getByText("Bad range")).toBeVisible();
    rerender(<RouterProvider router={createMemoryRouter([{ path: "/reports", element: <ReportsPagination query={{ limit: 10, offset: 10, rangeError: null }} count={10} /> }], { initialEntries: ["/reports"] })} />);
    await userEvent.click(screen.getByRole("button", { name: "Previous" }));
    expect(router.state.location.pathname).toBe("/reports");
  });
});

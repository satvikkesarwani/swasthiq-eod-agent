import { screen, waitFor } from "@testing-library/dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { analyticsReport, healthyResponse, makeClinicDayReport, recentReportsResponse } from "../test/fixtures";
import { renderApp } from "../test/renderWithRouter";

vi.mock("../api/endpoints", () => {
  return { getHealth: vi.fn(), listClinicDays: vi.fn(), getClinicDay: vi.fn() };
});

describe("application shell and routes", () => {
  beforeEach(async () => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    const { getHealth, listClinicDays, getClinicDay } = await import("../api/endpoints");
    vi.mocked(getHealth).mockResolvedValue(healthyResponse);
    vi.mocked(listClinicDays).mockResolvedValue(recentReportsResponse);
    vi.mocked(getClinicDay).mockResolvedValue(makeClinicDayReport());
  });

  it("renders reports home with persistent navigation and topbar status", async () => {
    renderApp("/reports");

    expect(await screen.findByRole("banner")).toHaveTextContent("SwasthiQ EOD");
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
    expect(screen.getByRole("navigation", { name: "Mobile navigation" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Reports" })).toBeVisible();
    await waitFor(() => expect(screen.getByText("Test Clinic")).toBeVisible());
    await waitFor(() => expect(screen.getByText("Backend online")).toBeVisible());
  });

  it("renders guarded report detail pages when params are valid", async () => {
    const { getClinicDay } = await import("../api/endpoints");
    vi.mocked(getClinicDay).mockResolvedValueOnce(analyticsReport);
    renderApp("/reports/clinic-a/2026-07-31/analytics");

    expect(await screen.findByRole("heading", { name: "EOD Analytics" })).toBeVisible();
    expect(screen.getByLabelText("Analytics report context")).toHaveTextContent("CLN-TST-001");
    expect(screen.getByLabelText("Analytics report context")).toHaveTextContent("31 Jul 2026");
    await waitFor(() => expect(screen.getByText("Backend online")).toBeVisible());
  });

  it("renders the narrative placeholder without fabricated content", async () => {
    renderApp("/reports/clinic-a/2026-07-31/narrative");

    expect(screen.getByRole("heading", { name: "Narrative" })).toBeVisible();
    expect(screen.getByText("Narrative not generated")).toBeVisible();
    await waitFor(() => expect(screen.getByText("Backend online")).toBeVisible());
  });

  it("shows guard state for invalid report params", async () => {
    renderApp("/reports/clinic-a/not-a-date/reconciliation");

    expect(await screen.findByRole("alert")).toHaveTextContent("Report context unavailable");
    expect(screen.getByRole("link", { name: "Back to Reports" })).toHaveAttribute("href", "/reports");
    await waitFor(() => expect(screen.getByText("Backend online")).toBeVisible());
  });

  it("renders not found routes inside the shell", async () => {
    renderApp("/missing");

    expect(screen.getByRole("alert")).toHaveTextContent("Page not found");
    expect(screen.getByRole("link", { name: "Back to reports" })).toBeVisible();
    await waitFor(() => expect(screen.getByText("Backend online")).toBeVisible());
  });

  it("exposes skip navigation for keyboard users", async () => {
    renderApp("/reports");

    expect(await screen.findByRole("link", { name: "Skip to content" })).toHaveAttribute("href", "#main-content");
    await waitFor(() => expect(screen.getByText("Backend online")).toBeVisible());
  });
});

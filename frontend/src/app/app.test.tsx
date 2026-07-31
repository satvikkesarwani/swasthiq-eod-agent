import { screen, waitFor } from "@testing-library/dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { healthyResponse } from "../test/fixtures";
import { renderApp } from "../test/renderWithRouter";

vi.mock("../api/endpoints", () => {
  return { getHealth: vi.fn() };
});

describe("application shell and routes", () => {
  beforeEach(async () => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    const { getHealth } = await import("../api/endpoints");
    vi.mocked(getHealth).mockResolvedValue(healthyResponse);
  });

  it("renders reports home with persistent navigation and topbar status", async () => {
    renderApp("/reports");

    expect(screen.getByRole("banner")).toHaveTextContent("SwasthiQ EOD");
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
    expect(screen.getByRole("navigation", { name: "Mobile navigation" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Grounded EOD reports" })).toBeVisible();
    await waitFor(() => expect(screen.getByText("Backend online")).toBeVisible());
  });

  it("renders guarded report detail pages when params are valid", async () => {
    renderApp("/reports/clinic-a/2026-07-31/analytics");

    expect(screen.getByRole("heading", { name: "Analytics" })).toBeVisible();
    expect(screen.getByLabelText("Report context")).toHaveTextContent("clinic-a");
    expect(screen.getByLabelText("Report context")).toHaveTextContent("2026-07-31");
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

    expect(screen.getByRole("alert")).toHaveTextContent("Report context unavailable");
    expect(screen.getByRole("link", { name: "Back to reports" })).toHaveAttribute("href", "/reports");
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

    expect(screen.getByRole("link", { name: "Skip to content" })).toHaveAttribute("href", "#main-content");
    await waitFor(() => expect(screen.getByText("Backend online")).toBeVisible());
  });
});

import { screen } from "@testing-library/dom";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { createMemoryRouter, RouterProvider } from "react-router";
import type { ReactNode } from "react";

import { Badge } from "./Badge";
import { Button } from "./Button";
import { Divider } from "./Divider";
import { Drawer } from "./Drawer";
import { GlassPanel } from "./GlassPanel";
import { IconButton } from "./IconButton";
import { StatusPill } from "./StatusPill";

function renderWithMemoryRouter(element: ReactNode) {
  const router = createMemoryRouter([{ path: "/", element }], { initialEntries: ["/"] });
  return render(<RouterProvider router={router} />);
}

describe("design primitives", () => {
  it("renders buttons, badges, dividers and status pills accessibly", async () => {
    const onClick = vi.fn();
    renderWithMemoryRouter(
      <div>
        <Button onClick={onClick}>Run check</Button>
        <Button to="/reports" variant="primary">Open reports</Button>
        <IconButton label="Refresh">R</IconButton>
        <Badge>Contract</Badge>
        <Divider />
        <StatusPill tone="healthy">Healthy</StatusPill>
      </div>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Run check" }));
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("link", { name: "Open reports" })).toHaveAttribute("href", "/reports");
    expect(screen.getByRole("button", { name: "Refresh" })).toBeVisible();
    expect(screen.getByText("Healthy")).toBeVisible();
  });

  it("renders glass panels with semantic headings", () => {
    render(<GlassPanel title="Clinical panel" description="Foundation panel">Body</GlassPanel>);
    expect(screen.getByRole("heading", { name: "Clinical panel" })).toBeVisible();
    expect(screen.getByText("Foundation panel")).toBeVisible();
  });

  it("opens and closes drawers with focus return", async () => {
    const onClose = vi.fn();
    render(
      <div>
        <button type="button">Before</button>
        <Drawer open title="Filters" onClose={onClose}>Drawer body</Drawer>
      </div>,
    );

    expect(screen.getByRole("dialog", { name: "Filters" })).toBeVisible();
    await userEvent.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

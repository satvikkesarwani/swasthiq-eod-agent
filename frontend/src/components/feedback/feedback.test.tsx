import { screen } from "@testing-library/dom";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InlineError } from "./InlineError";
import { LoadingSkeleton } from "./LoadingSkeleton";
import { OfflineBanner } from "./OfflineBanner";
import { ToastRegion } from "./ToastRegion";

describe("feedback components", () => {
  it("renders offline, loading, inline error and toast states", () => {
    const { rerender } = render(
      <div>
        <OfflineBanner online={false} />
        <LoadingSkeleton rows={2} />
        <InlineError message="Validation failed" />
        <ToastRegion toasts={[{ id: "1", message: "Saved" }]} />
      </div>,
    );

    expect(screen.getByText("Network connection unavailable")).toBeVisible();
    expect(screen.getByLabelText("Loading")).toHaveAttribute("aria-busy", "true");
    expect(screen.getByText("Validation failed")).toBeVisible();
    expect(screen.getByText("Saved")).toBeVisible();

    rerender(<OfflineBanner online />);
    expect(screen.queryByText("Network connection unavailable")).not.toBeInTheDocument();
  });
});

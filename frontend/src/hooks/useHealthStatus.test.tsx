import { waitFor } from "@testing-library/dom";
import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { healthyResponse } from "../test/fixtures";
import { useHealthStatus } from "./useHealthStatus";

vi.mock("../api/endpoints", () => ({
  getHealth: vi.fn(),
}));

describe("useHealthStatus", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.restoreAllMocks();
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
  });

  it("reports a healthy backend response", async () => {
    const { getHealth } = await import("../api/endpoints");
    vi.mocked(getHealth).mockResolvedValue(healthyResponse);

    const { result } = renderHook(() => useHealthStatus());

    expect(result.current.state).toBe("checking");
    await waitFor(() => expect(result.current.state).toBe("healthy"));
    expect(result.current.label).toBe("Backend online");
  });

  it("reports unavailable when the health request fails", async () => {
    const { getHealth } = await import("../api/endpoints");
    vi.mocked(getHealth).mockRejectedValue(new Error("down"));

    const { result } = renderHook(() => useHealthStatus());

    await waitFor(() => expect(result.current.state).toBe("unavailable"));
  });
});

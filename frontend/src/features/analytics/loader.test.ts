import type { LoaderFunctionArgs } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../api/client";
import { getClinicDay } from "../../api/endpoints";
import { analyticsReport } from "../../test/fixtures";
import { analyticsLoader } from "./loader";

vi.mock("../../api/endpoints", () => ({ getClinicDay: vi.fn() }));

function loaderArgs(path = "http://localhost/reports/CLN%20A/2026-07-31/analytics", params = { clinicId: "CLN A", businessDate: "2026-07-31" }) {
  const controller = new AbortController();
  return {
    request: new Request(path, { signal: controller.signal }),
    params,
    context: {},
    url: new URL(path),
    pattern: {},
  } as unknown as LoaderFunctionArgs;
}

describe("analytics loader", () => {
  beforeEach(() => {
    vi.mocked(getClinicDay).mockReset();
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
  });

  it("loads canonical clinic-day detail with preserved params and AbortSignal", async () => {
    vi.mocked(getClinicDay).mockResolvedValue(analyticsReport);

    const result = await analyticsLoader(loaderArgs());

    expect(result).toEqual({ state: "ready", report: analyticsReport });
    expect(getClinicDay).toHaveBeenCalledWith("CLN A", "2026-07-31", expect.any(AbortSignal));
  });

  it("does not call the API for invalid params", async () => {
    await expect(analyticsLoader(loaderArgs("http://localhost/bad", { clinicId: "", businessDate: "bad" }))).resolves.toMatchObject({ state: "error", title: "Report context unavailable" });
    expect(getClinicDay).not.toHaveBeenCalled();
  });

  it("returns controlled states for 404, network, 500 and malformed responses", async () => {
    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("Missing", 404, "NOT_FOUND", "req404"));
    await expect(analyticsLoader(loaderArgs())).resolves.toMatchObject({ state: "not_found" });

    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("No network", 0, "NETWORK_ERROR", null));
    await expect(analyticsLoader(loaderArgs())).resolves.toMatchObject({ state: "error", title: "The billing service could not be reached." });

    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("Oops", 500, "INTERNAL_ERROR", "req500"));
    await expect(analyticsLoader(loaderArgs())).resolves.toMatchObject({ state: "error", requestId: "req500" });

    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("Bad JSON", 200, "MALFORMED_JSON", null));
    await expect(analyticsLoader(loaderArgs())).resolves.toMatchObject({ state: "error", title: "The analytics response could not be verified." });
  });

  it("contains structurally invalid analytics as a page error", async () => {
    vi.mocked(getClinicDay).mockResolvedValue({
      ...analyticsReport,
      report: {
        ...analyticsReport.report,
        analytics: {
          ...analyticsReport.report.analytics,
          peak_hour: { start_hour_utc: 9, end_hour_utc: 10, revenue_paise: 50.5 },
        },
      },
    });

    await expect(analyticsLoader(loaderArgs())).resolves.toMatchObject({ state: "error", title: "The analytics response could not be verified." });
  });
});

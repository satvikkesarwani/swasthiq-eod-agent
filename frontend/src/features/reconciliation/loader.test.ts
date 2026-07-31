import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../api/client";
import { getClinicDay } from "../../api/endpoints";
import { makeClinicDayReport } from "../../test/fixtures";
import { reconciliationLoader } from "./loader";

vi.mock("../../api/endpoints", () => ({ getClinicDay: vi.fn() }));

function loaderArgs(path = "http://localhost/reports/CLN%20A/2026-07-31/reconciliation", params = { clinicId: "CLN A", businessDate: "2026-07-31" }) {
  const controller = new AbortController();
  return {
    request: new Request(path, { signal: controller.signal }),
    params,
    context: {},
    url: new URL(path),
    pattern: {},
  } as unknown as LoaderFunctionArgs;
}

describe("reconciliation loader", () => {
  beforeEach(() => {
    vi.mocked(getClinicDay).mockReset();
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
  });

  it("loads canonical clinic-day detail with preserved params and AbortSignal", async () => {
    const report = makeClinicDayReport();
    vi.mocked(getClinicDay).mockResolvedValue(report);

    const result = await reconciliationLoader(loaderArgs());

    expect(result).toEqual({ state: "ready", report });
    expect(getClinicDay).toHaveBeenCalledWith("CLN A", "2026-07-31", expect.any(AbortSignal));
  });

  it("does not call the API for invalid params", async () => {
    await expect(reconciliationLoader(loaderArgs("http://localhost/bad", { clinicId: "", businessDate: "bad" }))).resolves.toMatchObject({ state: "error", title: "Report context unavailable" });
    expect(getClinicDay).not.toHaveBeenCalled();
  });

  it("returns controlled states for 404, network, 500 and malformed responses", async () => {
    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("Missing", 404, "NOT_FOUND", "req404"));
    await expect(reconciliationLoader(loaderArgs())).resolves.toMatchObject({ state: "not_found" });

    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("No network", 0, "NETWORK_ERROR", null));
    await expect(reconciliationLoader(loaderArgs())).resolves.toMatchObject({ state: "error", title: "The billing service could not be reached." });

    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("Oops", 500, "INTERNAL_ERROR", "req500"));
    await expect(reconciliationLoader(loaderArgs())).resolves.toMatchObject({ state: "error", requestId: "req500" });

    vi.mocked(getClinicDay).mockRejectedValueOnce(new ApiError("Bad JSON", 200, "MALFORMED_JSON", null));
    await expect(reconciliationLoader(loaderArgs())).resolves.toMatchObject({ state: "error", title: "The report response could not be verified." });
  });
});
import type { LoaderFunctionArgs } from "react-router";

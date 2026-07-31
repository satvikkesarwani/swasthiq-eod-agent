import { describe, expect, it, vi, beforeEach } from "vitest";
import type { LoaderFunctionArgs } from "react-router";

import { ApiError } from "../../api/client";
import { listClinicDays } from "../../api/endpoints";
import { recentReportsResponse } from "../../test/fixtures";
import { reportsLoader } from "./loader";

vi.mock("../../api/endpoints", () => ({ listClinicDays: vi.fn() }));

function args(url = "http://localhost/reports"): LoaderFunctionArgs {
  return {
    request: new Request(url),
    params: {},
    context: {},
    url: new URL(url),
    pattern: {},
  } as unknown as LoaderFunctionArgs;
}

describe("reportsLoader", () => {
  beforeEach(() => {
    vi.mocked(listClinicDays).mockReset();
  });

  it("loads recent reports with bounded query params", async () => {
    vi.mocked(listClinicDays).mockResolvedValue(recentReportsResponse);
    const result = await reportsLoader(args("http://localhost/reports?clinic_id=CLN&date_from=2026-07-01&date_to=2026-07-31&offset=10"));

    expect(result.response).toBe(recentReportsResponse);
    expect(result.error).toBeNull();
    expect(result.query.clinicId).toBe("CLN");
    expect(result.query.offset).toBe(10);
    expect(listClinicDays).toHaveBeenCalledWith(expect.objectContaining({ clinicId: "CLN", dateFrom: "2026-07-01", dateTo: "2026-07-31", limit: 10, offset: 10 }), expect.any(AbortSignal));
  });

  it("returns an in-page range error without calling the API", async () => {
    const result = await reportsLoader(args("http://localhost/reports?date_from=2026-08-01&date_to=2026-07-31"));

    expect(result).toMatchObject({ response: null, error: "Date from cannot be after date to." });
    expect(listClinicDays).not.toHaveBeenCalled();
  });

  it("maps network and service errors into safe panel errors", async () => {
    vi.mocked(listClinicDays).mockRejectedValueOnce(new ApiError("Network", 0, "NETWORK_ERROR", null));
    await expect(reportsLoader(args())).resolves.toMatchObject({ response: null, error: "The billing service could not be reached. Check that the backend is running, then refresh reports." });

    vi.mocked(listClinicDays).mockRejectedValueOnce(new ApiError("Server", 500, "INTERNAL_ERROR", "req1"));
    await expect(reportsLoader(args())).resolves.toMatchObject({ response: null, error: "Recent reports could not be loaded. Try again from the reports workspace." });
  });
});

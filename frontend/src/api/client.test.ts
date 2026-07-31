import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiUrl, normalizeApiBase, requestJson } from "./client";
import { generateNarrative, getClinicDay, getClinicDayErrors, getHealth, getNarrative, listClinicDays, putClinicDay } from "./endpoints";

describe("api client", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("normalizes API base URLs and appends the contract prefix", () => {
    expect(normalizeApiBase("https://example.test/api/v1/")).toBe("https://example.test");
    expect(apiUrl("/health")).toBe("/api/v1/health");
  });

  it("sends JSON requests through native fetch", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(requestJson<{ status: string }>("/health")).resolves.toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/health", expect.objectContaining({
      method: "GET",
      credentials: "same-origin",
    }));
  });

  it("maps backend error envelopes into ApiError", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      error: { code: "BAD_INPUT", message: "Invalid clinic", request_id: "req-1", details: [{ field: "clinic_id" }] },
    }), { status: 422 })));

    await expect(requestJson("/clinic-days")).rejects.toMatchObject({
      name: "ApiError",
      status: 422,
      code: "BAD_INPUT",
      requestId: "req-1",
    });
  });

  it("raises network and malformed JSON errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    await expect(requestJson("/health")).rejects.toBeInstanceOf(ApiError);

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{", { status: 200 })));
    await expect(requestJson("/health")).rejects.toMatchObject({ code: "MALFORMED_JSON" });
  });

  it("falls back to the local backend in dev when the same-origin proxy is unavailable", async () => {
    Object.defineProperty(window, "location", {
      configurable: true,
      value: new URL("http://127.0.0.1:5173/reports"),
    });
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("proxy refused"))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: "healthy" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(requestJson<{ status: string }>("/health")).resolves.toEqual({ status: "healthy" });
    expect(fetchMock.mock.calls.map(([url]) => String(url))).toEqual([
      "/api/v1/health",
      "http://127.0.0.1:8000/api/v1/health",
    ]);
  });

  it("builds typed endpoint paths", async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 })));
    vi.stubGlobal("fetch", fetchMock);

    await getHealth();
    await listClinicDays({ clinicId: "clinic/a", limit: 10, offset: 5 });
    await getClinicDay("clinic/a", "2026-07-31");
    await putClinicDay("clinic/a", "2026-07-31", { records: [] });
    await getClinicDayErrors("clinic/a", "2026-07-31", { limit: 5 });
    await getNarrative("clinic/a", "2026-07-31");
    await generateNarrative("clinic/a", "2026-07-31");

    const requestedUrls = fetchMock.mock.calls.map(([url]) => String(url));
    expect(requestedUrls).toEqual([
      "/api/v1/health",
      "/api/v1/clinic-days?clinic_id=clinic%2Fa&limit=10&offset=5",
      "/api/v1/clinic-days/clinic%2Fa/2026-07-31",
      "/api/v1/clinic-days/clinic%2Fa/2026-07-31",
      "/api/v1/clinic-days/clinic%2Fa/2026-07-31/errors?limit=5",
      "/api/v1/clinic-days/clinic%2Fa/2026-07-31/narrative",
      "/api/v1/clinic-days/clinic%2Fa/2026-07-31/narrative",
    ]);
  });
});

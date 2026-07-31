import type { HealthResponse } from "../api/types";

export const healthyResponse: HealthResponse = {
  status: "ok",
  version: "test",
  database: "ok",
};

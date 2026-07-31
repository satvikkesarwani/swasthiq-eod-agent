import type { LoaderFunctionArgs } from "react-router";

import { ApiError } from "../../api/client";
import { listClinicDays } from "../../api/endpoints";
import { parseReportsQuery } from "./queryParams";

export async function reportsLoader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const query = parseReportsQuery(url.search);
  if (query.rangeError) {
    return { query, response: null, error: query.rangeError };
  }
  try {
    const response = await listClinicDays({
      ...(query.clinicId ? { clinicId: query.clinicId } : {}),
      ...(query.dateFrom ? { dateFrom: query.dateFrom } : {}),
      ...(query.dateTo ? { dateTo: query.dateTo } : {}),
      limit: query.limit,
      offset: query.offset,
    }, request.signal);
    return { query, response, error: null };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    if (error instanceof ApiError && (error.status === 0 || error.code === "NETWORK_ERROR")) {
      return { query, response: null, error: "The billing service could not be reached. Check that the backend is running, then refresh reports." };
    }
    return { query, response: null, error: "Recent reports could not be loaded. Try again from the reports workspace." };
  }
}

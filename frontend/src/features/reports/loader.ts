import type { LoaderFunctionArgs } from "react-router";

import { listClinicDays } from "../../api/endpoints";
import { parseReportsQuery } from "./queryParams";

export async function reportsLoader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const query = parseReportsQuery(url.search);
  if (query.rangeError) {
    return { query, response: null, error: query.rangeError };
  }
  const response = await listClinicDays({
    ...(query.clinicId ? { clinicId: query.clinicId } : {}),
    ...(query.dateFrom ? { dateFrom: query.dateFrom } : {}),
    ...(query.dateTo ? { dateTo: query.dateTo } : {}),
    limit: query.limit,
    offset: query.offset,
  }, request.signal);
  return { query, response, error: null };
}

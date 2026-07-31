import type { LoaderFunctionArgs } from "react-router";

import { getClinicDay } from "../../api/endpoints";
import { ApiError } from "../../api/client";
import type { ReconciliationLoaderData } from "./types";
import { validateReportParams } from "./presentation";

function failureMessage(error: unknown): Pick<Extract<ReconciliationLoaderData, { state: "error" }>, "title" | "message" | "requestId"> {
  if (typeof navigator !== "undefined" && navigator.onLine === false) {
    return { title: "You appear to be offline.", message: "Reconnect and try loading the report again.", requestId: null };
  }
  if (error instanceof ApiError) {
    if (error.status === 500) {
      return { title: "The billing service could not load this report.", message: "Try again. Internal details have been hidden.", requestId: error.requestId };
    }
    if (error.status === 0 || error.code === "NETWORK_ERROR") {
      return { title: "The billing service could not be reached.", message: "Check the backend connection and try again.", requestId: error.requestId };
    }
    if (error.code === "MALFORMED_JSON") {
      return { title: "The report response could not be verified.", message: "The service returned data the app could not safely read.", requestId: error.requestId };
    }
    return { title: "The billing service could not load this report.", message: "Try again from the latest stored report.", requestId: error.requestId };
  }
  return { title: "The report response could not be verified.", message: "The report response could not be safely verified.", requestId: null };
}

export async function reconciliationLoader({ params, request }: LoaderFunctionArgs): Promise<ReconciliationLoaderData> {
  const candidateParams: { clinicId?: string; businessDate?: string } = {};
  if (params.clinicId !== undefined) {
    candidateParams.clinicId = params.clinicId;
  }
  if (params.businessDate !== undefined) {
    candidateParams.businessDate = params.businessDate;
  }
  const validated = validateReportParams(candidateParams);
  if (!validated) {
    return {
      state: "error",
      clinicId: params.clinicId ?? "Unavailable",
      businessDate: params.businessDate ?? "Unavailable",
      title: "Report context unavailable",
      message: "Open a report from the reports workspace so the clinic and business date can be verified.",
      requestId: null,
    };
  }

  try {
    const report = await getClinicDay(validated.clinicId, validated.businessDate, request.signal);
    return { state: "ready", report };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    if (error instanceof ApiError && error.status === 404) {
      return { state: "not_found", clinicId: validated.clinicId, businessDate: validated.businessDate };
    }
    return { state: "error", clinicId: validated.clinicId, businessDate: validated.businessDate, ...failureMessage(error) };
  }
}

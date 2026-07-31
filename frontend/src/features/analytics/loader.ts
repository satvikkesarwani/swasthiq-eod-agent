import type { LoaderFunctionArgs } from "react-router";

import { ApiError } from "../../api/client";
import { getClinicDay } from "../../api/endpoints";
import { logDiagnostic } from "../../lib/diagnostics";
import { validateReportParams } from "../reconciliation/presentation";
import { validateAnalyticsContract } from "./presentation";
import type { AnalyticsLoaderData } from "./types";

function failure(error: unknown): Pick<Extract<AnalyticsLoaderData, { state: "error" }>, "title" | "message" | "requestId"> {
  if (typeof navigator !== "undefined" && navigator.onLine === false) {
    return { title: "You appear to be offline.", message: "Reconnect and try loading analytics again.", requestId: null };
  }
  if (error instanceof ApiError) {
    if (error.status === 0 || error.code === "NETWORK_ERROR") {
      return { title: "The billing service could not be reached.", message: "Check that the backend is running, then try again.", requestId: error.requestId };
    }
    if (error.status === 500) {
      return { title: "The billing service could not load analytics for this report.", message: "Try again. Internal details have been hidden.", requestId: error.requestId };
    }
    if (error.code === "MALFORMED_JSON") {
      return { title: "The analytics response could not be verified.", message: "The service returned data the app could not safely read.", requestId: error.requestId };
    }
  }
  return { title: "The analytics response could not be verified.", message: "The report analytics could not be safely verified.", requestId: null };
}

export async function analyticsLoader({ params, request }: LoaderFunctionArgs): Promise<AnalyticsLoaderData> {
  logDiagnostic("info", "analytics.loader", "Analytics loader start", {
    clinicId: params.clinicId,
    businessDate: params.businessDate,
  });
  const routeParams: { clinicId?: string; businessDate?: string } = {};
  if (params.clinicId !== undefined) {
    routeParams.clinicId = params.clinicId;
  }
  if (params.businessDate !== undefined) {
    routeParams.businessDate = params.businessDate;
  }
  const validated = validateReportParams(routeParams);
  if (!validated) {
    logDiagnostic("warn", "analytics.loader", "Analytics route params invalid", {
      clinicId: params.clinicId,
      businessDate: params.businessDate,
    });
    return { state: "error", clinicId: params.clinicId ?? "Unavailable", businessDate: params.businessDate ?? "Unavailable", title: "Report context unavailable", message: "Open analytics from a stored report so the clinic and business date can be verified.", requestId: null };
  }

  try {
    const report = await getClinicDay(validated.clinicId, validated.businessDate, request.signal);
    const malformed = validateAnalyticsContract(report);
    if (malformed) {
      logDiagnostic("warn", "analytics.loader", "Analytics contract invalid", {
        clinicId: validated.clinicId,
        businessDate: validated.businessDate,
        malformed,
      });
      return { state: "error", clinicId: validated.clinicId, businessDate: validated.businessDate, title: malformed, message: "The report analytics could not be safely verified.", requestId: null };
    }
    logDiagnostic("info", "analytics.loader", "Analytics loader ready", {
      clinicId: validated.clinicId,
      businessDate: validated.businessDate,
      receivedRows: report.ingestion.received_rows,
      acceptedRows: report.ingestion.accepted_rows,
      rejectedRows: report.ingestion.rejected_rows,
      totalBilledPaise: report.report.reconciliation.total_billed_paise,
      totalRefundsPaise: report.report.reconciliation.total_refunds_paise,
      positiveHours: report.report.analytics.revenue_by_hour.filter((bucket) => bucket.revenue_paise > 0).length,
      topQuantity: report.report.analytics.top_medicines_by_quantity.length,
      topRevenue: report.report.analytics.top_medicines_by_revenue.length,
    });
    return { state: "ready", report };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    if (error instanceof ApiError && error.status === 404) {
      logDiagnostic("warn", "analytics.loader", "Analytics report not found", {
        clinicId: validated.clinicId,
        businessDate: validated.businessDate,
        requestId: error.requestId,
      });
      return { state: "not_found", clinicId: validated.clinicId, businessDate: validated.businessDate };
    }
    logDiagnostic("error", "analytics.loader", "Analytics loader failed", {
      clinicId: validated.clinicId,
      businessDate: validated.businessDate,
      error,
    });
    return { state: "error", clinicId: validated.clinicId, businessDate: validated.businessDate, ...failure(error) };
  }
}

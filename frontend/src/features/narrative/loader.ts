import type { LoaderFunctionArgs } from "react-router";

import { ApiError } from "../../api/client";
import { getClinicDay, getNarrative } from "../../api/endpoints";
import { logDiagnostic } from "../../lib/diagnostics";
import { validateReportParams } from "../reconciliation/presentation";
import { validateNarrativeContract } from "./presentation";
import type { NarrativeLoaderData, NarrativeResource } from "./types";

function loadFailure(error: unknown): { title: string; message: string; requestId: string | null } {
  if (typeof navigator !== "undefined" && navigator.onLine === false) {
    return { title: "You appear to be offline.", message: "Reconnect and try loading the summary again.", requestId: null };
  }
  if (error instanceof ApiError) {
    if (error.status === 0 || error.code === "NETWORK_ERROR") {
      return { title: "The billing service could not be reached.", message: "Check the backend connection and try again.", requestId: error.requestId };
    }
    if (error.code === "MALFORMED_JSON") {
      return { title: "The summary response could not be verified.", message: "The service returned data the app could not safely read.", requestId: error.requestId };
    }
    return { title: "The billing service could not load this summary.", message: "Try again. Internal details have been hidden.", requestId: error.requestId };
  }
  return { title: "The summary response could not be verified.", message: "The report summary could not be safely verified.", requestId: null };
}

async function loadNarrative(clinicId: string, businessDate: string, signal: AbortSignal): Promise<NarrativeResource> {
  try {
    const narrative = await getNarrative(clinicId, businessDate, signal);
    const invalid = validateNarrativeContract(narrative);
    if (invalid) {
      return { state: "error", title: invalid, message: "The summary response could not be safely verified.", requestId: null };
    }
    return { state: "available", source: "cached", narrative };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    if (error instanceof ApiError && (error.status === 404 || error.code === "NARRATIVE_NOT_GENERATED")) {
      return { state: "not_generated" };
    }
    if (error instanceof ApiError && error.code === "NARRATIVE_STALE") {
      return { state: "not_generated" };
    }
    const failure = loadFailure(error);
    return { state: "error", ...failure };
  }
}

export async function narrativeLoader({ params, request }: LoaderFunctionArgs): Promise<NarrativeLoaderData> {
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
      message: "Open the AI summary from a stored report so the clinic and business date can be verified.",
      requestId: null,
    };
  }

  try {
    logDiagnostic("info", "narrative.loader", "Narrative route load started", {
      clinicId: validated.clinicId,
      businessDate: validated.businessDate,
    });
    const report = await getClinicDay(validated.clinicId, validated.businessDate, request.signal);
    const narrative = await loadNarrative(validated.clinicId, validated.businessDate, request.signal);
    logDiagnostic("info", "narrative.loader", "Narrative route load completed", {
      clinicId: validated.clinicId,
      businessDate: validated.businessDate,
      narrativeState: narrative.state,
      reportNarrativeStatus: report.narrative_status,
    });
    return { state: "ready", report, narrative };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    if (error instanceof ApiError && error.status === 404) {
      return { state: "not_found", clinicId: validated.clinicId, businessDate: validated.businessDate };
    }
    logDiagnostic("error", "narrative.loader", "Narrative route load failed", {
      clinicId: validated.clinicId,
      businessDate: validated.businessDate,
      error,
    });
    return { state: "error", clinicId: validated.clinicId, businessDate: validated.businessDate, ...loadFailure(error) };
  }
}

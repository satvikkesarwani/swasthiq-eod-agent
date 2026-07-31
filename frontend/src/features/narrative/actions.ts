import { ApiError } from "../../api/client";
import { generateNarrative } from "../../api/endpoints";
import type { NarrativeResponse } from "../../api/types";
import { logDiagnostic } from "../../lib/diagnostics";
import { validateNarrativeContract } from "./presentation";

export async function requestNarrativeGeneration(
  clinicId: string,
  businessDate: string,
  forceRegenerate: boolean,
  signal?: AbortSignal,
): Promise<NarrativeResponse> {
  logDiagnostic("info", "narrative.action", "Narrative generation started", {
    clinicId,
    businessDate,
    forceRegenerate,
  });
  try {
    const narrative = await generateNarrative(clinicId, businessDate, { force_regenerate: forceRegenerate }, signal);
    const invalid = validateNarrativeContract(narrative);
    if (invalid) {
      logDiagnostic("warn", "narrative.action", "Narrative generation response invalid", {
        clinicId,
        businessDate,
        status: narrative.status,
        traceCount: narrative.traces?.length,
      });
      throw new ApiError(invalid, 0, "MALFORMED_NARRATIVE_RESPONSE", null);
    }
    logDiagnostic("info", "narrative.action", "Narrative generation completed", {
      clinicId,
      businessDate,
      status: narrative.status,
      traceCount: narrative.traces.length,
      fallbackReasonCode: narrative.fallback_reason_code,
    });
    return narrative;
  } catch (error) {
    if (!(error instanceof DOMException && error.name === "AbortError")) {
      logDiagnostic("error", "narrative.action", "Narrative generation failed", {
        clinicId,
        businessDate,
        error,
      });
    }
    throw error;
  }
}

import type { ClinicDayDetail, NarrativeResponse } from "../../api/types";

export type NarrativeResource =
  | { state: "available"; source: "cached"; narrative: NarrativeResponse }
  | { state: "not_generated" }
  | { state: "error"; title: string; message: string; requestId: string | null };

export type NarrativeLoaderData =
  | { state: "ready"; report: ClinicDayDetail; narrative: NarrativeResource }
  | { state: "not_found"; clinicId: string; businessDate: string }
  | { state: "error"; clinicId: string; businessDate: string; title: string; message: string; requestId: string | null };

export type NarrativeMutationState =
  | { state: "idle"; error: null; requestId: null }
  | { state: "generating"; forceRegenerate: boolean; error: null; requestId: null }
  | { state: "failed"; error: string; requestId: string | null };

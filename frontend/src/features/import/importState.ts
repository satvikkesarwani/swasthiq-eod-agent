import type { BillingFileError, ImportResult, ImportStatus, ParsedBillingFile } from "./types";

export type ImportState = {
  status: ImportStatus;
  token: number;
  parsedFile: ParsedBillingFile | null;
  fileError: BillingFileError | null;
  submitError: string | null;
  importResult: ImportResult | null;
};

export type ImportAction =
  | { type: "start_reading"; token: number }
  | { type: "file_ready"; token: number; parsedFile: ParsedBillingFile }
  | { type: "file_failed"; token: number; error: BillingFileError }
  | { type: "remove_file" }
  | { type: "start_submit"; token: number }
  | { type: "submit_success"; token: number; result: ImportResult }
  | { type: "submit_failed"; token: number; error: string }
  | { type: "form_changed" }
  | { type: "reset" };

export const initialImportState: ImportState = {
  status: "idle",
  token: 0,
  parsedFile: null,
  fileError: null,
  submitError: null,
  importResult: null,
};

export function importReducer(state: ImportState, action: ImportAction): ImportState {
  if ("token" in action && action.token !== state.token && action.type !== "start_reading" && action.type !== "start_submit") {
    return state;
  }

  switch (action.type) {
    case "start_reading":
      return { ...initialImportState, status: "reading_file", token: action.token };
    case "file_ready":
      return { ...state, status: "file_ready", parsedFile: action.parsedFile, fileError: null, submitError: null, importResult: null };
    case "file_failed":
      return { ...state, status: "failed", parsedFile: null, fileError: action.error, submitError: null, importResult: null };
    case "remove_file":
      return { ...initialImportState, token: state.token + 1 };
    case "start_submit":
      if (state.status === "submitting" || state.parsedFile === null) {
        return state;
      }
      return { ...state, status: "submitting", token: action.token, submitError: null };
    case "submit_success":
      return {
        ...state,
        status: action.result.rejectedRows > 0 ? "completed_with_errors" : "completed",
        submitError: null,
        importResult: action.result,
      };
    case "submit_failed":
      return { ...state, status: state.parsedFile ? "file_ready" : "failed", submitError: action.error };
    case "form_changed":
      if (state.status === "completed" || state.status === "completed_with_errors") {
        return { ...state, status: state.parsedFile ? "file_ready" : "idle", importResult: null, submitError: null };
      }
      return { ...state, submitError: null };
    case "reset":
      return { ...initialImportState, token: state.token + 1 };
  }
}

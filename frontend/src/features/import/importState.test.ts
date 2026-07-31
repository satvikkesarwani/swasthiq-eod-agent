import { describe, expect, it } from "vitest";

import { createdImportResponse } from "../../test/fixtures";
import { mapImportResult } from "./importMapping";
import { importReducer, initialImportState } from "./importState";

const parsedFile = { fileName: "a.json", fileSizeBytes: 2, records: [], rowCount: 0, isEmpty: true };

describe("importReducer", () => {
  it("walks the import state machine and blocks stale responses", () => {
    let state = importReducer(initialImportState, { type: "start_reading", token: 1 });
    expect(state.status).toBe("reading_file");
    state = importReducer(state, { type: "file_ready", token: 1, parsedFile });
    expect(state.status).toBe("file_ready");
    const stale = importReducer(state, { type: "file_failed", token: 0, error: { code: "INVALID_JSON", message: "bad" } });
    expect(stale).toBe(state);
    state = importReducer(state, { type: "start_submit", token: 2 });
    expect(state.status).toBe("submitting");
    state = importReducer(state, { type: "submit_success", token: 2, result: mapImportResult(createdImportResponse) });
    expect(state.status).toBe("completed");
    state = importReducer(state, { type: "form_changed" });
    expect(state.status).toBe("file_ready");
  });

  it("preserves parsed files after submit failure and resets new files", () => {
    let state = importReducer(initialImportState, { type: "start_reading", token: 1 });
    state = importReducer(state, { type: "file_ready", token: 1, parsedFile });
    state = importReducer(state, { type: "start_submit", token: 2 });
    state = importReducer(state, { type: "submit_failed", token: 2, error: "failed" });
    expect(state.parsedFile).toBe(parsedFile);
    expect(state.status).toBe("file_ready");
    state = importReducer(state, { type: "remove_file" });
    expect(state.parsedFile).toBeNull();
  });
});

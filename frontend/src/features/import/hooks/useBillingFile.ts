import { useReducer, useRef } from "react";

import { importReducer, initialImportState } from "../importState";
import { BillingFileParseError, parseBillingLogFile } from "../parser";
import { validateDroppedFiles } from "../validation";
import type { BillingFileError } from "../types";
import { logDiagnostic } from "../../../lib/diagnostics";

export function useBillingFileState() {
  const [state, dispatch] = useReducer(importReducer, initialImportState);
  const tokenRef = useRef(0);

  const parseFile = (file: File) => {
    const token = tokenRef.current + 1;
    tokenRef.current = token;
    logDiagnostic("info", "import.file", "Start selected file parse", {
      token,
      fileName: file.name,
      fileSizeBytes: file.size,
      fileType: file.type,
    });
    dispatch({ type: "start_reading", token });

    void parseBillingLogFile(file).then(
      (parsedFile) => {
        logDiagnostic("info", "import.file", "Selected file ready", {
          token,
          fileName: parsedFile.fileName,
          rowCount: parsedFile.rowCount,
          isEmpty: parsedFile.isEmpty,
        });
        dispatch({ type: "file_ready", token, parsedFile });
      },
      (error: unknown) => {
        const safeError: BillingFileError = error instanceof BillingFileParseError
          ? { code: error.code, message: error.message }
          : { code: "FILE_READ_FAILED", message: "The selected file could not be read." };
        logDiagnostic("warn", "import.file", "Selected file failed", {
          token,
          code: safeError.code,
          message: safeError.message,
          error,
        });
        dispatch({ type: "file_failed", token, error: safeError });
      },
    );
  };

  const selectFiles = (files: FileList | File[]) => {
    logDiagnostic("info", "import.file", "Files selected", { count: files.length });
    const validation = validateDroppedFiles(files);
    if (validation !== null) {
      const token = tokenRef.current + 1;
      tokenRef.current = token;
      logDiagnostic("warn", "import.file", "Selected files rejected", {
        token,
        code: validation.code,
        message: validation.message,
        count: files.length,
      });
      dispatch({ type: "start_reading", token });
      dispatch({ type: "file_failed", token, error: validation });
      return;
    }
    const [file] = files;
    if (file) {
      parseFile(file);
    }
  };

  return { state, dispatch, selectFiles };
}

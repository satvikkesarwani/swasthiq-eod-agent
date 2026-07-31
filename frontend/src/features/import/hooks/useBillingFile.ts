import { useReducer, useRef } from "react";

import { importReducer, initialImportState } from "../importState";
import { BillingFileParseError, parseBillingLogFile } from "../parser";
import { validateDroppedFiles } from "../validation";
import type { BillingFileError } from "../types";

export function useBillingFileState() {
  const [state, dispatch] = useReducer(importReducer, initialImportState);
  const tokenRef = useRef(0);

  const parseFile = (file: File) => {
    const token = tokenRef.current + 1;
    tokenRef.current = token;
    dispatch({ type: "start_reading", token });

    void parseBillingLogFile(file).then(
      (parsedFile) => dispatch({ type: "file_ready", token, parsedFile }),
      (error: unknown) => {
        const safeError: BillingFileError = error instanceof BillingFileParseError
          ? { code: error.code, message: error.message }
          : { code: "FILE_READ_FAILED", message: "The selected file could not be read." };
        dispatch({ type: "file_failed", token, error: safeError });
      },
    );
  };

  const selectFiles = (files: FileList | File[]) => {
    const validation = validateDroppedFiles(files);
    if (validation !== null) {
      const token = tokenRef.current + 1;
      tokenRef.current = token;
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

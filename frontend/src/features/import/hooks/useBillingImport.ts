import { useEffect, useRef, type Dispatch } from "react";
import { useNavigate, useRevalidator } from "react-router";

import { putClinicDay } from "../../../api/endpoints";
import { useAppContext } from "../../../app/AppContext";
import { reportRoutes } from "../../../app/routes";
import type { BillingLogRequest } from "../../../api/types";
import { logDiagnostic } from "../../../lib/diagnostics";
import { mapImportError } from "../errorMapping";
import { mapImportResult } from "../importMapping";
import type { ImportAction, ImportState } from "../importState";
import { isEstimatedRequestTooLarge } from "../requestPolicy";
import { trimOptional } from "../validation";

type SubmitImportInput = {
  clinicId: string;
  clinicName: string;
  clinicLocation: string;
  businessDate: string;
};

export function useBillingImport(state: ImportState, dispatch: Dispatch<ImportAction>) {
  const navigate = useNavigate();
  const revalidator = useRevalidator();
  const { pushToast } = useAppContext();
  const tokenRef = useRef(state.token);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    tokenRef.current = state.token;
  }, [state.token]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const submitImport = async (input: SubmitImportInput) => {
    if (state.status === "submitting" || state.parsedFile === null) {
      logDiagnostic("warn", "import.submit", "Submit ignored", {
        status: state.status,
        hasFile: state.parsedFile !== null,
      });
      return;
    }

    const clinicName = trimOptional(input.clinicName);
    const clinicLocation = trimOptional(input.clinicLocation);
    const payload: BillingLogRequest = { records: state.parsedFile.records };
    if (clinicName) {
      payload.clinic_name = clinicName;
    }
    if (clinicLocation) {
      payload.clinic_location = clinicLocation;
    }

    if (isEstimatedRequestTooLarge(payload)) {
      logDiagnostic("warn", "import.submit", "Submit blocked by estimated request size", {
        clinicId: input.clinicId,
        businessDate: input.businessDate,
        rowCount: state.parsedFile.rowCount,
      });
      dispatch({
        type: "submit_failed",
        token: state.token,
        error: "The final JSON request is estimated to exceed the 5 MiB service limit. Choose a smaller file.",
      });
      return;
    }

    const token = state.token + 1;
    tokenRef.current = token;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    logDiagnostic("info", "import.submit", "Submit start", {
      token,
      clinicId: input.clinicId,
      businessDate: input.businessDate,
      clinicNamePresent: clinicName !== undefined,
      clinicLocationPresent: clinicLocation !== undefined,
      rowCount: state.parsedFile.rowCount,
      isEmpty: state.parsedFile.isEmpty,
    });
    dispatch({ type: "start_submit", token });

    try {
      const response = await putClinicDay(input.clinicId, input.businessDate, payload, controller.signal);
      if (token !== tokenRef.current) {
        logDiagnostic("warn", "import.submit", "Submit response ignored due to stale token", {
          token,
          currentToken: tokenRef.current,
        });
        return;
      }
      const result = mapImportResult(response);
      logDiagnostic("info", "import.submit", "Submit success", {
        token,
        clinicId: result.clinicId,
        businessDate: result.businessDate,
        operation: result.operation,
        status: result.status,
        acceptedRows: result.acceptedRows,
        rejectedRows: result.rejectedRows,
      });
      dispatch({ type: "submit_success", token, result });
      await revalidator.revalidate();

      if (result.rejectedRows === 0) {
        const message = result.operation === "unchanged"
          ? "Submitted billing log matches the existing report."
          : result.operation === "replaced"
            ? "Billing log replaced successfully."
            : "Billing log processed successfully. Opening the EOD report.";
        pushToast(message);
        void navigate(reportRoutes.reconciliation(result.clinicId, result.businessDate), {
          state: {
            operation: result.operation,
            status: result.status,
            acceptedRows: result.acceptedRows,
            rejectedRows: result.rejectedRows,
          },
        });
      } else {
        pushToast("Report generated with validation issues.");
      }
    } catch (error) {
      if (token !== tokenRef.current) {
        logDiagnostic("warn", "import.submit", "Submit error ignored due to stale token", {
          token,
          currentToken: tokenRef.current,
          error,
        });
        return;
      }
      const mapped = mapImportError(error);
      if (mapped === null) {
        logDiagnostic("warn", "import.submit", "Submit aborted", { token, error });
        return;
      }
      logDiagnostic("error", "import.submit", "Submit failed", {
        token,
        clinicId: input.clinicId,
        businessDate: input.businessDate,
        code: mapped.code,
        message: mapped.message,
        requestId: mapped.requestId,
        detailsCount: mapped.details.length,
        error,
      });
      dispatch({ type: "submit_failed", token, error: `${mapped.message}${mapped.requestId ? ` Request ID: ${mapped.requestId}` : ""}` });
      pushToast("Import failed.");
    }
  };

  return { submitImport, abortImport: () => abortRef.current?.abort() };
}

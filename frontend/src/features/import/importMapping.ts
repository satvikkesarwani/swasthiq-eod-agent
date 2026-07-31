import type { ClinicDayDetail } from "../../api/types";
import type { ImportResult } from "./types";

export function mapImportResult(response: ClinicDayDetail): ImportResult {
  return {
    operation: response.operation ?? "updated",
    status: response.status,
    clinicId: response.clinic_id,
    businessDate: response.business_date,
    receivedRows: response.ingestion.received_rows,
    acceptedRows: response.ingestion.accepted_rows,
    rejectedRows: response.ingestion.rejected_rows,
    reportHash: response.report_hash,
    warnings: response.report.data_quality_warnings.map((warning) => warning.message),
    response,
  };
}

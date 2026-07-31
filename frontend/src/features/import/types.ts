import type { ClinicDayDetail, IngestionIssue } from "../../api/types";

export type ParsedBillingFile = {
  fileName: string;
  fileSizeBytes: number;
  records: unknown[];
  rowCount: number;
  isEmpty: boolean;
};

export type BillingFileErrorCode =
  | "NO_FILE"
  | "MULTIPLE_FILES"
  | "UNSUPPORTED_FILE"
  | "FILE_TOO_LARGE"
  | "FILE_READ_FAILED"
  | "EMPTY_FILE"
  | "INVALID_JSON"
  | "ROOT_NOT_ARRAY";

export type BillingFileError = {
  code: BillingFileErrorCode;
  message: string;
};

export type ImportStatus = "idle" | "reading_file" | "file_ready" | "submitting" | "completed" | "completed_with_errors" | "failed";

export type ImportResult = {
  operation: string;
  status: string;
  clinicId: string;
  businessDate: string;
  receivedRows: number;
  acceptedRows: number;
  rejectedRows: number;
  reportHash: string;
  warnings: string[];
  response: ClinicDayDetail;
};

export type SafeIssue = IngestionIssue;

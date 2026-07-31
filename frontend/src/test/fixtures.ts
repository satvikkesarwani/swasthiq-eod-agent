import type { HealthResponse } from "../api/types";
import type { ClinicDayDetail, ClinicDayListResponse, ClinicDaySummary, IngestionIssueListResponse } from "../api/types";

export const healthyResponse: HealthResponse = {
  status: "ok",
  version: "test",
  database: "ok",
};

export const validSalesRecords = [
  { clinic_id: "CLN-TST-001", visit_id: "v1", timestamp: "2026-07-31T09:00:00Z", doctor_id: "d1", line_items: [{ drug_name: "ORS", qty: 1, unit_price_paise: 1000 }], payment_mode: "cash", amount_paid_paise: 1000, discount_paise: 0, is_refund: false },
];

export const partialMalformedRecords = [
  validSalesRecords[0],
  "malformed row stays here",
  { visit_id: "missing clinic" },
];

export const recentReport: ClinicDaySummary = {
  clinic_id: "CLN-TST-001",
  clinic_name: "Test Clinic",
  business_date: "2026-07-31",
  status: "completed",
  accepted_rows: 1,
  rejected_rows: 0,
  narrative_status: "not_generated",
  report_hash: "sha256:test",
  total_billed_paise: 1000,
  total_collected_paise: 1000,
  total_outstanding_paise: 0,
  total_refunds_paise: 0,
  updated_at: "2026-07-31T10:00:00Z",
};

export const recentReportsResponse: ClinicDayListResponse = {
  count: 1,
  items: [recentReport],
  limit: 10,
  offset: 0,
};

export const createdImportResponse: ClinicDayDetail = {
  clinic_id: "CLN-TST-001",
  clinic_name: "Test Clinic",
  clinic_location: null,
  business_date: "2026-07-31",
  status: "completed",
  operation: "created",
  ingestion: { received_rows: 1, accepted_rows: 1, rejected_rows: 0 },
  report: {
    reconciliation: {
      total_billed_paise: 1000,
      total_collected_paise: 1000,
      total_outstanding_paise: 0,
      total_refunds_paise: 0,
      total_discount_paise: 0,
      collection_rate: 1,
      by_payment_mode: {},
      refund_visit_count: 0,
      pending_visit_count: 0,
    },
    analytics: { peak_hour: null, revenue_by_hour: [], top_medicines_by_quantity: [], top_medicines_by_revenue: [] },
    data_quality_warnings: [],
  },
  source_hash: "sha256:source",
  report_hash: "sha256:report",
  narrative_status: "not_generated",
  created_at: "2026-07-31T10:00:00Z",
  updated_at: "2026-07-31T10:00:00Z",
};

export const partialImportResponse: ClinicDayDetail = {
  ...createdImportResponse,
  status: "completed_with_errors",
  operation: "replaced",
  ingestion: { received_rows: 3, accepted_rows: 1, rejected_rows: 2 },
};

export const safeIssuesResponse: IngestionIssueListResponse = {
  clinic_id: "CLN-TST-001",
  business_date: "2026-07-31",
  count: 1,
  limit: 20,
  offset: 0,
  errors: [
    { row_index: 1, visit_id: "v-bad", field_path: "line_items", error_code: "INVALID_ROW", message: "Line items are invalid." },
  ],
};

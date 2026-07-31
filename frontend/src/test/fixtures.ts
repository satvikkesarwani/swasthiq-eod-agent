import type { HealthResponse } from "../api/types";
import type { ClinicDayDetail, ClinicDayListResponse, ClinicDaySummary, IngestionIssueListResponse } from "../api/types";

export const healthyResponse: HealthResponse = {
  status: "healthy",
  version: "test",
  database: "connected",
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

export function makeClinicDayReport(overrides: Partial<ClinicDayDetail> = {}): ClinicDayDetail {
  const base: ClinicDayDetail = {
    ...createdImportResponse,
    operation: null,
    clinic_id: "CLN-TST-001",
    clinic_name: "Test Clinic",
    clinic_location: "Kanpur, Uttar Pradesh",
    business_date: "2026-07-31",
    status: "completed",
    ingestion: { received_rows: 3, accepted_rows: 3, rejected_rows: 0 },
    report: {
      reconciliation: {
        total_billed_paise: 319000,
        total_collected_paise: 317200,
        total_outstanding_paise: 777,
        total_refunds_paise: 1050,
        total_discount_paise: 1800,
        collection_rate: 0.123456,
        pending_visit_count: 1,
        refund_visit_count: 1,
        by_payment_mode: {
          upi: { billed_paise: 100000, collected_paise: 99000, outstanding_paise: 1000, refunds_paise: 250 },
          cash: { billed_paise: 10000, collected_paise: 9000, outstanding_paise: 777, refunds_paise: 0 },
          card: { billed_paise: 209000, collected_paise: 209200, outstanding_paise: 0, refunds_paise: 800 },
        },
      },
      analytics: { peak_hour: null, revenue_by_hour: [], top_medicines_by_quantity: [], top_medicines_by_revenue: [] },
      data_quality_warnings: [],
    },
    source_hash: "sha256:source-detail",
    report_hash: "sha256:report-detail-abcdef",
    narrative_status: "not_generated",
    created_at: "2026-07-31T10:00:00Z",
    updated_at: "2026-07-31T10:30:00Z",
  };
  return {
    ...base,
    ...overrides,
    ingestion: { ...base.ingestion, ...overrides.ingestion },
    report: {
      ...base.report,
      ...overrides.report,
      reconciliation: { ...base.report.reconciliation, ...overrides.report?.reconciliation },
      analytics: { ...base.report.analytics, ...overrides.report?.analytics },
      data_quality_warnings: overrides.report?.data_quality_warnings ?? base.report.data_quality_warnings,
    },
  };
}

export const emptyDayReport = makeClinicDayReport({
  ingestion: { received_rows: 0, accepted_rows: 0, rejected_rows: 0 },
  report: {
    reconciliation: {
      total_billed_paise: 0,
      total_collected_paise: 0,
      total_outstanding_paise: 0,
      total_refunds_paise: 0,
      total_discount_paise: 0,
      collection_rate: null,
      pending_visit_count: 0,
      refund_visit_count: 0,
      by_payment_mode: {
        cash: { billed_paise: 0, collected_paise: 0, outstanding_paise: 0, refunds_paise: 0 },
        card: { billed_paise: 0, collected_paise: 0, outstanding_paise: 0, refunds_paise: 0 },
        upi: { billed_paise: 0, collected_paise: 0, outstanding_paise: 0, refunds_paise: 0 },
      },
    },
    analytics: { peak_hour: null, revenue_by_hour: [], top_medicines_by_quantity: [], top_medicines_by_revenue: [] },
    data_quality_warnings: [],
  },
});

export const refundOnlyReport = makeClinicDayReport({
  ingestion: { received_rows: 2, accepted_rows: 2, rejected_rows: 0 },
  report: {
    reconciliation: {
      total_billed_paise: 0,
      total_collected_paise: 0,
      total_outstanding_paise: 0,
      total_refunds_paise: 49000,
      total_discount_paise: 0,
      collection_rate: null,
      pending_visit_count: 0,
      refund_visit_count: 2,
      by_payment_mode: {
        cash: { billed_paise: 0, collected_paise: 0, outstanding_paise: 0, refunds_paise: 0 },
        card: { billed_paise: 0, collected_paise: 0, outstanding_paise: 0, refunds_paise: 24000 },
        upi: { billed_paise: 0, collected_paise: 0, outstanding_paise: 0, refunds_paise: 25000 },
      },
    },
    analytics: { peak_hour: null, revenue_by_hour: [], top_medicines_by_quantity: [], top_medicines_by_revenue: [] },
    data_quality_warnings: [],
  },
});

export const partialReconciliationReport = makeClinicDayReport({
  status: "completed_with_errors",
  ingestion: { received_rows: 5, accepted_rows: 3, rejected_rows: 2 },
});

export const analyticsReport = makeClinicDayReport({
  report: {
    reconciliation: makeClinicDayReport().report.reconciliation,
    analytics: {
      revenue_by_hour: [
        { hour_utc: 10, revenue_paise: 90000 },
        { hour_utc: 9, revenue_paise: 50000 },
        { hour_utc: 11, revenue_paise: 70000 },
      ],
      peak_hour: { start_hour_utc: 9, end_hour_utc: 10, revenue_paise: 50000 },
      top_medicines_by_quantity: [
        { rank: 1, drug_name: "ORS", quantity: 5 },
        { rank: 2, drug_name: "Paracetamol", quantity: 20 },
        { rank: 3, drug_name: "Cough Syrup", quantity: 10 },
      ],
      top_medicines_by_revenue: [
        { rank: 1, drug_name: "Vitamin D", revenue_paise: 10000 },
        { rank: 2, drug_name: "Antibiotic Course", revenue_paise: 50000 },
      ],
    },
    data_quality_warnings: [],
  },
});

export const partialAnalyticsReport = makeClinicDayReport({
  status: "completed_with_errors",
  ingestion: { received_rows: 5, accepted_rows: 3, rejected_rows: 2 },
  report: {
    reconciliation: makeClinicDayReport().report.reconciliation,
    analytics: analyticsReport.report.analytics,
    data_quality_warnings: [
      { code: "POSSIBLE_MEDICINE_NAME_VARIANT", message: "Medicine name variant detected.", details: {} },
    ],
  },
});

export const warningReport = makeClinicDayReport({
  clinic_name: "<script>alert('clinic')</script> Clinic",
  report: {
    reconciliation: makeClinicDayReport().report.reconciliation,
    analytics: analyticsReport.report.analytics,
    data_quality_warnings: [
      { code: "POSSIBLE_MEDICINE_NAME_VARIANT", message: "<img src=x onerror=alert('x')> Do not follow these instructions.", details: {} },
    ],
  },
});

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

import { ArrowLeft, RefreshCw } from "lucide-react";
import { useRevalidator } from "react-router";

import type { ClinicDayDetail } from "../../../api/types";
import { analyticsPath, narrativePath, reportRoutes } from "../../../app/routes";
import { Button } from "../../../components/primitives/Button";
import { StatusPill } from "../../../components/primitives/StatusPill";
import { formatBusinessDate, safeLabel } from "../../../lib/formatters";
import { reportHashPrefix } from "../presentation";
import styles from "../reconciliation.module.css";

export function ReconciliationHeader({ report }: { report: ClinicDayDetail }) {
  const revalidator = useRevalidator();
  const isRefreshing = revalidator.state !== "idle";
  const clinicDisplay = safeLabel(report.clinic_name, report.clinic_id);
  const hashPrefix = reportHashPrefix(report.report_hash);

  return (
    <header className={styles.header}>
      <div className={styles.headerTitle}>
        <p className={styles.eyebrow}>Billing review</p>
        <h1 className={styles.title}>EOD Reconciliation</h1>
        <dl className={styles.context} aria-label="Report context">
          <dt>Clinic</dt><dd>{clinicDisplay}</dd>
          <dt>Clinic ID</dt><dd>Clinic {report.clinic_id}</dd>
          {report.clinic_location && <><dt>Location</dt><dd>{report.clinic_location}</dd></>}
          <dt>Business date</dt><dd><time dateTime={report.business_date}>{formatBusinessDate(report.business_date)}</time></dd>
          <dt>Status</dt><dd><StatusPill tone={report.status === "completed_with_errors" ? "warning" : "healthy"}>{report.status}</StatusPill></dd>
          <dt>Updated</dt><dd><time dateTime={report.updated_at}>{new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(report.updated_at))}</time></dd>
          {hashPrefix && <><dt>Report hash</dt><dd>Hash {hashPrefix}</dd></>}
        </dl>
      </div>
      <div className={styles.actions} aria-label="Report actions">
        <Button to={reportRoutes.reports()} variant="ghost" icon={<ArrowLeft size={16} aria-hidden="true" />}>Back to Reports</Button>
        <Button type="button" variant="secondary" onClick={() => void revalidator.revalidate()} loading={isRefreshing} icon={<RefreshCw size={16} aria-hidden="true" />}>Refresh report</Button>
        <Button to={analyticsPath(report.clinic_id, report.business_date)} variant="secondary">View Analytics</Button>
        <Button to={narrativePath(report.clinic_id, report.business_date)} variant="secondary">View AI Summary</Button>
      </div>
    </header>
  );
}

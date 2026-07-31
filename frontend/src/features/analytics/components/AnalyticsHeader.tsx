import { ArrowLeft, FileText, RefreshCw } from "lucide-react";
import { useRevalidator } from "react-router";

import type { ClinicDayDetail } from "../../../api/types";
import { narrativePath, reconciliationPath, reportRoutes } from "../../../app/routes";
import { Button } from "../../../components/primitives/Button";
import { StatusPill } from "../../../components/primitives/StatusPill";
import { formatBusinessDate, safeLabel } from "../../../lib/formatters";
import { shortHash } from "../presentation";
import styles from "../analytics.module.css";

export function AnalyticsHeader({ report }: { report: ClinicDayDetail }) {
  const revalidator = useRevalidator();
  const isRefreshing = revalidator.state !== "idle";
  const clinicDisplay = safeLabel(report.clinic_name, report.clinic_id);
  const hashPrefix = shortHash(report.report_hash);

  return (
    <header className={styles.header}>
      <div className={styles.headerTitle}>
        <p className={styles.eyebrow}>Operational analytics</p>
        <h1 className={styles.title}>EOD Analytics</h1>
        <dl className={styles.context} aria-label="Analytics report context">
          <dt>Clinic</dt><dd>{clinicDisplay}</dd>
          <dt>Clinic ID</dt><dd>Clinic {report.clinic_id}</dd>
          {report.clinic_location && <><dt>Location</dt><dd>{report.clinic_location}</dd></>}
          <dt>Business date</dt><dd><time dateTime={report.business_date}>{formatBusinessDate(report.business_date)}</time></dd>
          <dt>Status</dt><dd><StatusPill tone={report.status === "completed_with_errors" ? "warning" : "healthy"}>{report.status}</StatusPill></dd>
          <dt>Report hash</dt><dd>Hash {hashPrefix}</dd>
        </dl>
      </div>
      <div className={styles.actions} aria-label="Analytics actions">
        <Button to={reportRoutes.reports()} variant="ghost" icon={<ArrowLeft size={16} aria-hidden="true" />}>Back to Reports</Button>
        <Button type="button" variant="secondary" onClick={() => void revalidator.revalidate()} loading={isRefreshing} icon={<RefreshCw size={16} aria-hidden="true" />}>Refresh analytics</Button>
        <Button to={reconciliationPath(report.clinic_id, report.business_date)} variant="secondary" icon={<FileText size={16} aria-hidden="true" />}>View Reconciliation</Button>
        <Button to={narrativePath(report.clinic_id, report.business_date)} variant="secondary">View AI Summary</Button>
      </div>
    </header>
  );
}

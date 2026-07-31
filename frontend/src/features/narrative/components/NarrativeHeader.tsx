import { ArrowLeft, BarChart3, FileText, RefreshCw } from "lucide-react";
import { useRevalidator } from "react-router";

import type { ClinicDayDetail, NarrativeResponse } from "../../../api/types";
import { analyticsPath, reconciliationPath, reportRoutes } from "../../../app/routes";
import { Button } from "../../../components/primitives/Button";
import { StatusPill } from "../../../components/primitives/StatusPill";
import { formatBusinessDate, safeLabel } from "../../../lib/formatters";
import { narrativeStatusLabel, narrativeStatusTone, reportHashPrefix } from "../presentation";
import styles from "../narrative.module.css";

type NarrativeHeaderProps = {
  report: ClinicDayDetail;
  narrative: NarrativeResponse | null;
  source: "cached" | "generated" | null;
};

export function NarrativeHeader({ report, narrative, source }: NarrativeHeaderProps) {
  const revalidator = useRevalidator();
  const isRefreshing = revalidator.state !== "idle";
  const clinicDisplay = safeLabel(report.clinic_name, report.clinic_id);

  return (
    <header className={styles.header}>
      <div className={styles.headerTitle}>
        <p className={styles.eyebrow}>Grounded narrative</p>
        <h1 className={styles.title}>AI Narrative Summary</h1>
        <dl className={styles.context} aria-label="Narrative report context">
          <dt>Clinic</dt><dd>{clinicDisplay}</dd>
          <dt>Clinic ID</dt><dd>Clinic {report.clinic_id}</dd>
          {report.clinic_location && <><dt>Location</dt><dd>{report.clinic_location}</dd></>}
          <dt>Business date</dt><dd><time dateTime={report.business_date}>{formatBusinessDate(report.business_date)}</time></dd>
          <dt>Report status</dt><dd><StatusPill tone={report.status === "completed_with_errors" ? "warning" : "healthy"}>{report.status}</StatusPill></dd>
          <dt>Narrative status</dt><dd><StatusPill tone={narrativeStatusTone(narrative)}>{narrativeStatusLabel(narrative, source)}</StatusPill></dd>
          <dt>Updated</dt><dd><time dateTime={report.updated_at}>{new Date(report.updated_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}</time></dd>
          <dt>Report hash</dt><dd>Hash {reportHashPrefix(report.report_hash)}</dd>
        </dl>
      </div>
      <div className={styles.actions} aria-label="Narrative actions">
        <Button to={reportRoutes.reports()} variant="ghost" icon={<ArrowLeft size={16} aria-hidden="true" />}>Back to Reports</Button>
        <Button type="button" variant="secondary" onClick={() => void revalidator.revalidate()} loading={isRefreshing} icon={<RefreshCw size={16} aria-hidden="true" />}>Refresh</Button>
        <Button to={reconciliationPath(report.clinic_id, report.business_date)} variant="secondary" icon={<FileText size={16} aria-hidden="true" />}>Reconciliation</Button>
        <Button to={analyticsPath(report.clinic_id, report.business_date)} variant="secondary" icon={<BarChart3 size={16} aria-hidden="true" />}>Analytics</Button>
      </div>
    </header>
  );
}

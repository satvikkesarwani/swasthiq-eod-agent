import type { ClinicDayDetail } from "../../../api/types";
import { Button } from "../../../components/primitives/Button";
import { formatCount } from "../../../lib/formatters";
import { reportHashPrefix } from "../presentation";
import styles from "../reconciliation.module.css";

export function ReportIntegrityPanel({ report, onReviewIssues }: { report: ClinicDayDetail; onReviewIssues: () => void }) {
  const hashPrefix = reportHashPrefix(report.report_hash);
  return (
    <div className={styles.healthStack}>
      <p className={styles.muted}>Financial totals on this page come from the deterministic billing report.</p>
      <div className={styles.integrityGrid}>
        <div className={styles.integrityItem}><span>Status</span><strong>{report.status}</strong></div>
        <div className={styles.integrityItem}><span>Received rows</span><strong>{formatCount(report.ingestion.received_rows)}</strong></div>
        <div className={styles.integrityItem}><span>Accepted rows</span><strong>{formatCount(report.ingestion.accepted_rows)}</strong></div>
        <div className={styles.integrityItem}><span>Rejected rows</span><strong>{formatCount(report.ingestion.rejected_rows)}</strong></div>
        <div className={styles.integrityItem}><span>Narrative</span><strong>{report.narrative_status}</strong></div>
        {hashPrefix && <div className={styles.integrityItem}><span>Report hash</span><strong>{hashPrefix}</strong></div>}
      </div>
      {report.ingestion.rejected_rows > 0 && (
        <div className={styles.actions}>
          <Button type="button" variant="secondary" size="small" onClick={onReviewIssues}>Review validation issues</Button>
        </div>
      )}
    </div>
  );
}

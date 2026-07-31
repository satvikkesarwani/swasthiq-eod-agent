import { AlertTriangle } from "lucide-react";

import type { ClinicDayDetail } from "../../../api/types";
import { Button } from "../../../components/primitives/Button";
import { formatCount } from "../../../lib/formatters";
import styles from "../reconciliation.module.css";

export function ImportQualityBanner({ report, onReviewIssues }: { report: ClinicDayDetail; onReviewIssues: () => void }) {
  if (report.ingestion.rejected_rows <= 0 || report.ingestion.accepted_rows <= 0) {
    return null;
  }
  return (
    <section className={styles.qualityBanner} role="status" aria-labelledby="partial-import-title">
      <AlertTriangle aria-hidden="true" />
      <div>
        <h2 id="partial-import-title">Report generated from accepted rows</h2>
        <p>
          {formatCount(report.ingestion.accepted_rows)} accepted rows are included. {formatCount(report.ingestion.rejected_rows)} rejected rows are excluded from all totals and analytics.
        </p>
        <div className={styles.actions}>
          <Button type="button" variant="secondary" size="small" onClick={onReviewIssues}>Review validation issues</Button>
        </div>
      </div>
    </section>
  );
}

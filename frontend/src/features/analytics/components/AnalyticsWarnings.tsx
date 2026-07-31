import { AlertTriangle } from "lucide-react";

import type { ClinicDayDetail } from "../../../api/types";
import styles from "../analytics.module.css";

export function AnalyticsWarnings({ report }: { report: ClinicDayDetail }) {
  const warnings = report.report.data_quality_warnings;
  if (warnings.length === 0) {
    return <p className={styles.muted}>No data-quality warnings were generated for this analytics view.</p>;
  }
  return (
    <ul className={styles.warningList} aria-label="Analytics data quality warnings">
      {warnings.map((warning) => (
        <li key={`${warning.code}-${warning.message}`}>
          <AlertTriangle size={18} aria-hidden="true" /> <strong>{warning.code}</strong>
          <p className={styles.muted}>{warning.message}</p>
        </li>
      ))}
    </ul>
  );
}

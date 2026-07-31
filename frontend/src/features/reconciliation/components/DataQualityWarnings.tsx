import { AlertTriangle } from "lucide-react";

import type { ClinicDayDetail } from "../../../api/types";
import styles from "../reconciliation.module.css";

export function DataQualityWarnings({ report }: { report: ClinicDayDetail }) {
  const warnings = report.report.data_quality_warnings;
  if (warnings.length === 0) {
    return <p className={styles.muted}>No data-quality warnings were generated for this report.</p>;
  }
  return (
    <ul className={styles.warningList} aria-label="Data quality warnings">
      {warnings.map((warning) => (
        <li key={`${warning.code}-${warning.message}`}>
          <AlertTriangle size={18} aria-hidden="true" /> <strong>{warning.code}</strong>
          <p className={styles.muted}>{warning.message}</p>
        </li>
      ))}
    </ul>
  );
}

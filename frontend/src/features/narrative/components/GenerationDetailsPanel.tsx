import type { ClinicDayDetail, NarrativeResponse } from "../../../api/types";
import { fallbackReasonLabel, narrativeStatusLabel, reportHashPrefix } from "../presentation";
import styles from "../narrative.module.css";

export function GenerationDetailsPanel({ report, narrative, source }: { report: ClinicDayDetail; narrative: NarrativeResponse | null; source: "cached" | "generated" | null }) {
  return (
    <dl className={styles.detailsGrid} aria-label="Generation details">
      <div className={styles.detailItem}>
        <span>Status</span>
        <strong>{narrativeStatusLabel(narrative, source)}</strong>
      </div>
      <div className={styles.detailItem}>
        <span>Provider</span>
        <strong>{narrative?.provider ?? "Not called"}</strong>
      </div>
      <div className={styles.detailItem}>
        <span>Model</span>
        <strong>{narrative?.model ?? "Not available"}</strong>
      </div>
      <div className={styles.detailItem}>
        <span>Generation time</span>
        <strong>{narrative?.generation_ms === null || narrative?.generation_ms === undefined ? "Not available" : `${narrative.generation_ms} ms`}</strong>
      </div>
      <div className={styles.detailItem}>
        <span>Report hash</span>
        <code>{reportHashPrefix(narrative?.report_hash ?? report.report_hash)}</code>
      </div>
      <div className={styles.detailItem}>
        <span>Fallback reason</span>
        <strong>{fallbackReasonLabel(narrative?.fallback_reason_code)}</strong>
      </div>
    </dl>
  );
}

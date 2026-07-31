import type { ClinicDayDetail } from "../../../api/types";
import { GlassPanel } from "../../../components/primitives/GlassPanel";
import { formatCount } from "../../../lib/formatters";
import { shortHash } from "../presentation";
import styles from "../analytics.module.css";

export function AnalyticsDefinitionsPanel({ report }: { report: ClinicDayDetail }) {
  return (
    <GlassPanel title="Report Integrity" description="Read-only report context from the stored clinic day.">
      <div className={styles.integrityGrid}>
        <div className={styles.integrityItem}>
          <span>Accepted rows</span>
          <strong>{formatCount(report.ingestion.accepted_rows)}</strong>
        </div>
        <div className={styles.integrityItem}>
          <span>Rejected rows</span>
          <strong>{formatCount(report.ingestion.rejected_rows)}</strong>
        </div>
        <div className={styles.integrityItem}>
          <span>Report hash</span>
          <strong>{shortHash(report.report_hash)}</strong>
        </div>
      </div>
      <dl className={styles.definitionList}>
        <dt>Revenue by hour</dt>
        <dd>Backend billed-sales revenue bucketed by UTC hour.</dd>
        <dt>Peak billing hour</dt>
        <dd>The backend selected peak hour, when available.</dd>
        <dt>Medicine rankings</dt>
        <dd>Backend ordered medicine rankings by quantity and revenue.</dd>
      </dl>
    </GlassPanel>
  );
}

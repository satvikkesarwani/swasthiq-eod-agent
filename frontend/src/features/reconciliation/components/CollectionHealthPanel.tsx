import type { ClinicDayDetail } from "../../../api/types";
import { formatCount, formatPaise } from "../../../lib/formatters";
import { StatusPill } from "../../../components/primitives/StatusPill";
import { collectionRateVisualPercent, formatCollectionRate, getCollectionHealth } from "../presentation";
import styles from "../reconciliation.module.css";

export function CollectionHealthPanel({ report }: { report: ClinicDayDetail }) {
  const reconciliation = report.report.reconciliation;
  const health = getCollectionHealth(report);
  const rateLabel = formatCollectionRate(reconciliation.collection_rate);
  const visualRate = collectionRateVisualPercent(reconciliation.collection_rate);

  return (
    <div className={styles.healthStack}>
      <StatusPill tone={health.tone}>{health.label}</StatusPill>
      <p className={styles.healthLabel}>{rateLabel}</p>
      <p className={styles.muted}>{health.description}</p>
      <div
        className={styles.progressTrack}
        role="progressbar"
        aria-label="Backend supplied collection rate"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={visualRate}
        aria-valuetext={rateLabel}
      >
        <div className={styles.progressFill} style={{ width: `${visualRate}%` }} />
      </div>
      <div className={styles.integrityGrid}>
        <div className={styles.integrityItem}><span>Outstanding</span><strong>{formatPaise(reconciliation.total_outstanding_paise)}</strong></div>
        <div className={styles.integrityItem}><span>Pending visits</span><strong>{formatCount(reconciliation.pending_visit_count)}</strong></div>
        <div className={styles.integrityItem}><span>Refund visits</span><strong>{formatCount(reconciliation.refund_visit_count)}</strong></div>
        <div className={styles.integrityItem}><span>Discounts</span><strong>{formatPaise(reconciliation.total_discount_paise)}</strong></div>
      </div>
    </div>
  );
}

import { GlassPanel } from "../../../components/primitives/GlassPanel";
import styles from "../reconciliation.module.css";

export function ReconciliationSkeleton() {
  return (
    <div className={styles.skeleton} aria-label="Loading reconciliation report" aria-busy="true">
      <div className={styles.skeletonBlock} />
      <div className={styles.metricsGrid}>
        <div className={styles.skeletonBlock} />
        <div className={styles.skeletonBlock} />
        <div className={styles.skeletonBlock} />
        <div className={styles.skeletonBlock} />
      </div>
      <div className={styles.mainGrid}>
        <GlassPanel><div className={styles.skeletonBlock} /></GlassPanel>
        <GlassPanel><div className={styles.skeletonBlock} /></GlassPanel>
      </div>
    </div>
  );
}

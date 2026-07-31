import { GlassPanel } from "../../../components/primitives/GlassPanel";
import styles from "../analytics.module.css";

export function AnalyticsSkeleton() {
  return (
    <div className={styles.skeleton} aria-label="Loading analytics report" aria-busy="true">
      <div className={styles.skeletonBlock} />
      <div className={styles.summaryGrid}>
        <div className={styles.skeletonBlock} />
        <div className={styles.skeletonBlock} />
      </div>
      <div className={styles.dashboardGrid}>
        <GlassPanel><div className={styles.skeletonBlock} /></GlassPanel>
        <GlassPanel><div className={styles.skeletonBlock} /></GlassPanel>
      </div>
    </div>
  );
}

import styles from "../narrative.module.css";

export function NarrativeSkeleton() {
  return (
    <div className={styles.skeleton} aria-busy="true" aria-label="Loading narrative">
      <div className={styles.skeletonBlock} />
      <div className={styles.skeletonBlock} />
      <div className={styles.skeletonBlock} />
    </div>
  );
}

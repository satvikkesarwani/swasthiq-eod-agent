import styles from "./Feedback.module.css";

export function LoadingSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className={styles.skeletonStack} aria-label="Loading" aria-busy="true">
      {Array.from({ length: rows }, (_, index) => (
        <span key={index} className={styles.skeleton} style={{ width: `${96 - index * 10}%` }} />
      ))}
    </div>
  );
}

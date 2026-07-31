import type { NarrativeResponse } from "../../../api/types";
import styles from "../narrative.module.css";

export function UnavailableMetricsPanel({ narrative }: { narrative: NarrativeResponse | null }) {
  if (!narrative || narrative.unavailable_metrics.length === 0) {
    return <p className={styles.muted}>No unavailable metrics were returned for this summary.</p>;
  }
  return (
    <ul className={styles.metricList} aria-label="Unavailable metrics">
      {narrative.unavailable_metrics.map((metric, index) => (
        <li className={styles.metricItem} key={`${metric.metric}-${index}`}>
          <strong>{metric.metric}</strong>
          <p>{metric.reason}</p>
        </li>
      ))}
    </ul>
  );
}

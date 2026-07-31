import type { NarrativeResponse } from "../../../api/types";
import { rawValueLabel, traceLabel } from "../presentation";
import styles from "../narrative.module.css";

type Trace = NarrativeResponse["traces"][number];

export function TraceItem({ trace, index }: { trace: Trace; index: number }) {
  return (
    <li className={styles.traceItem}>
      <strong>{traceLabel(trace.report_path)}</strong>
      <span className={styles.traceValue}>{trace.display_value}</span>
      <code className={styles.tracePath}>{trace.report_path}</code>
      <span className={styles.traceMeta}>Trace {index + 1} · Raw value: {rawValueLabel(trace.raw_value)}</span>
    </li>
  );
}

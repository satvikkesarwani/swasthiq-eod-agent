import type { NarrativeResponse } from "../../../api/types";
import { TraceItem } from "./TraceItem";
import styles from "../narrative.module.css";

export function TracedFiguresPanel({ narrative }: { narrative: NarrativeResponse | null }) {
  if (!narrative || narrative.traces.length === 0) {
    return <p className={styles.muted}>No traced figures are available yet.</p>;
  }
  return (
    <>
      <ul className={styles.traceList} aria-label="Traced figures">
        {narrative.traces.map((trace, index) => (
          <TraceItem key={`${trace.report_path}-${trace.display_value}-${index}`} trace={trace} index={index} />
        ))}
      </ul>
      <p className={styles.muted}>Every figure above maps to the deterministic report.</p>
    </>
  );
}

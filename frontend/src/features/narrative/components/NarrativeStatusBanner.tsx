import type { ClinicDayDetail, NarrativeResponse } from "../../../api/types";
import { classNames } from "../../../lib/classNames";
import { fallbackReasonLabel, narrativeContext } from "../presentation";
import styles from "../narrative.module.css";

export function NarrativeStatusBanner({ report, narrative }: { report: ClinicDayDetail; narrative: NarrativeResponse | null }) {
  const context = narrativeContext(report);
  if (narrative?.status === "fallback") {
    return (
      <section className={classNames(styles.statusBanner, styles.fallback)} role="status">
        <div>
          <h2>Deterministic fallback summary</h2>
          <p>This summary was created using the built-in deterministic template because the AI provider was unavailable or its response could not be safely validated.</p>
          {narrative.fallback_reason_code && <p>Reason: {fallbackReasonLabel(narrative.fallback_reason_code)}</p>}
        </div>
      </section>
    );
  }
  return (
    <section className={classNames(styles.contextBanner, styles[context.kind])} role="status">
      <div>
        <h2>{context.title}</h2>
        <p>{context.message}</p>
      </div>
    </section>
  );
}

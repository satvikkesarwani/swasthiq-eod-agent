import { Copy } from "lucide-react";
import type { ReactNode } from "react";

import type { ClinicDayDetail, NarrativeResponse } from "../../../api/types";
import { Button } from "../../../components/primitives/Button";
import { StatusPill } from "../../../components/primitives/StatusPill";
import { narrativeStatusLabel, narrativeStatusTone } from "../presentation";
import type { NarrativeMutationState } from "../types";
import styles from "../narrative.module.css";

type NarrativeSummaryPanelProps = {
  report: ClinicDayDetail;
  narrative: NarrativeResponse | null;
  source: "cached" | "generated" | null;
  mutation: NarrativeMutationState;
  copyStatus: string;
  onCopy: () => void;
  controls: ReactNode;
};

export function NarrativeSummaryPanel({ narrative, source, mutation, copyStatus, onCopy, controls }: NarrativeSummaryPanelProps) {
  if (!narrative) {
    return (
      <div className={styles.emptySummary}>
        <div>
          <StatusPill tone="neutral">Not generated</StatusPill>
          <h2>No owner summary has been generated for this clinic day.</h2>
          <p className={styles.muted}>Generate a summary only when you want the backend to produce a grounded owner-facing message.</p>
        </div>
        {controls}
        {mutation.state === "failed" && <p role="alert" className={styles.muted}>{mutation.error}</p>}
      </div>
    );
  }

  return (
    <div className={styles.emptySummary}>
      <div>
        <StatusPill tone={narrativeStatusTone(narrative)}>{narrativeStatusLabel(narrative, source)}</StatusPill>
        <p className={styles.muted}>Every number in this summary is validated against backend traces.</p>
      </div>
      <p className={styles.summaryText}>{narrative.summary}</p>
      <div className={styles.buttonRow}>
        <Button type="button" variant="secondary" onClick={onCopy} icon={<Copy size={16} aria-hidden="true" />}>Copy Summary</Button>
        <span className={styles.muted}>Ready to paste into WhatsApp.</span>
      </div>
      <div className={styles.copyNotice} role="status" aria-live="polite">{copyStatus}</div>
      {controls}
      {mutation.state === "generating" && <p className={styles.muted}>Preparing a grounded owner summary...</p>}
      {mutation.state === "failed" && <p role="alert" className={styles.muted}>{mutation.error}</p>}
    </div>
  );
}

import { Clock3 } from "lucide-react";

import type { ClinicDayDetail } from "../../../api/types";
import { peakPresentation } from "../presentation";
import styles from "../analytics.module.css";

export function PeakHourCard({ report }: { report: ClinicDayDetail }) {
  const peak = peakPresentation(report);
  return (
    <section className={styles.peakCard} aria-label="Peak billing hour">
      <Clock3 size={20} aria-hidden="true" />
      <div>
        <p className={styles.muted}>{peak.title}</p>
        <strong>{peak.hour}</strong>
        <p>{peak.amount}</p>
        <p className={styles.muted}>{peak.explanation}</p>
      </div>
    </section>
  );
}

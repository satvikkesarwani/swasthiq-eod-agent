import { Info } from "lucide-react";

import type { ClinicDayDetail } from "../../../api/types";
import { getDayActivity } from "../presentation";
import styles from "../reconciliation.module.css";

export function ActivityBanner({ report }: { report: ClinicDayDetail }) {
  const activity = getDayActivity(report);
  if (activity.kind === "sales" || activity.kind === "partial") {
    return null;
  }
  return (
    <section className={styles.activityBanner} aria-labelledby="activity-title">
      <Info aria-hidden="true" />
      <div>
        <h2 id="activity-title">{activity.label}</h2>
        <p>{activity.description}</p>
      </div>
    </section>
  );
}

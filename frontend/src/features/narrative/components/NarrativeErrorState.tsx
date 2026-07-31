import { Link } from "react-router";

import { AppErrorState } from "../../../components/feedback/AppErrorState";
import type { NarrativeLoaderData } from "../types";
import styles from "../narrative.module.css";

export function NarrativeNotFound({ data }: { data: Extract<NarrativeLoaderData, { state: "not_found" }> }) {
  return (
    <div className={styles.errorPanel}>
      <AppErrorState
        title="Report not found"
        message={`No clinic-day report exists for ${data.clinicId} on ${data.businessDate}.`}
        action={<Link to="/reports">Back to Reports</Link>}
      />
    </div>
  );
}

export function NarrativeLoadError({ data }: { data: Extract<NarrativeLoaderData, { state: "error" }> }) {
  return (
    <div className={styles.errorPanel}>
      <AppErrorState title={data.title} message={data.message} action={<Link to="/reports">Back to Reports</Link>} />
      {data.requestId && <p className={styles.supportDetails}>Support request ID: <code>{data.requestId}</code></p>}
    </div>
  );
}

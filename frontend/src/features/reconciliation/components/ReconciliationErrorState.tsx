import { useRevalidator } from "react-router";

import { reportRoutes } from "../../../app/routes";
import { Button } from "../../../components/primitives/Button";
import type { ReconciliationLoaderData } from "../types";
import styles from "../reconciliation.module.css";

type ErrorData = Extract<ReconciliationLoaderData, { state: "error" }>;
type NotFoundData = Extract<ReconciliationLoaderData, { state: "not_found" }>;

export function ReconciliationNotFound({ data }: { data: NotFoundData }) {
  return (
    <section className={styles.errorPanel} role="alert" aria-labelledby="report-not-found-title">
      <h1 id="report-not-found-title">Report not found</h1>
      <p className={styles.muted}>No stored report was found for clinic {data.clinicId} on {data.businessDate}.</p>
      <div className={styles.actions}>
        <Button to={reportRoutes.reports()} variant="primary">Import billing log</Button>
        <Button to={reportRoutes.reports()} variant="secondary">Back to Reports</Button>
      </div>
    </section>
  );
}

export function ReconciliationLoadError({ data }: { data: ErrorData }) {
  const revalidator = useRevalidator();
  return (
    <section className={styles.errorPanel} role="alert" aria-labelledby="report-error-title">
      <h1 id="report-error-title">{data.title}</h1>
      <p className={styles.muted}>{data.message}</p>
      <div className={styles.actions}>
        <Button type="button" variant="primary" onClick={() => void revalidator.revalidate()} loading={revalidator.state !== "idle"}>Try again</Button>
        <Button to={reportRoutes.reports()} variant="secondary">Back to Reports</Button>
      </div>
      {data.requestId && (
        <details className={styles.supportDetails}>
          <summary>Support details</summary>
          <p>Request ID: <code>{data.requestId}</code></p>
        </details>
      )}
    </section>
  );
}

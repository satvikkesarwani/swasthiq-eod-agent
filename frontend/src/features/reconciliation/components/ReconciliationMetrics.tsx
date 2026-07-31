import type { ClinicDayDetail } from "../../../api/types";
import { mapMetrics } from "../presentation";
import { ReconciliationMetricCard } from "./ReconciliationMetricCard";
import styles from "../reconciliation.module.css";

export function ReconciliationMetrics({ report }: { report: ClinicDayDetail }) {
  return (
    <section aria-labelledby="financial-metrics-title">
      <h2 id="financial-metrics-title" className="sr-only">Financial metrics</h2>
      <div className={styles.metricsGrid}>
        {mapMetrics(report).map((metric) => <ReconciliationMetricCard key={metric.key} metric={metric} />)}
      </div>
    </section>
  );
}

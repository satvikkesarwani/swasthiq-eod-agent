import { Banknote, CircleDollarSign, CreditCard, ReceiptIndianRupee } from "lucide-react";

import { classNames } from "../../../lib/classNames";
import { formatPaise } from "../../../lib/formatters";
import type { MetricDefinition } from "../types";
import styles from "../reconciliation.module.css";

const icons = {
  billed: ReceiptIndianRupee,
  collected: CircleDollarSign,
  outstanding: CreditCard,
  refunds: Banknote,
};

export function ReconciliationMetricCard({ metric }: { metric: MetricDefinition }) {
  const Icon = icons[metric.key];
  return (
    <article className={classNames(styles.metricCard, styles[metric.accent])} aria-label={`${metric.label}: ${formatPaise(metric.valuePaise)}`}>
      <div className={styles.metricHeader}>
        <p className={styles.metricLabel}>{metric.label}</p>
        <span className={styles.metricIcon} aria-hidden="true"><Icon size={22} /></span>
      </div>
      <p className={styles.metricValue} data-value-paise={metric.valuePaise}>{formatPaise(metric.valuePaise)}</p>
      <p className={styles.metricDescription}>{metric.description}</p>
    </article>
  );
}

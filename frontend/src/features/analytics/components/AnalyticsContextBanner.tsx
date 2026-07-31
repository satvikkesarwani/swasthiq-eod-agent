import { AlertTriangle, BarChart3 } from "lucide-react";

import type { ClinicDayDetail } from "../../../api/types";
import { classNames } from "../../../lib/classNames";
import { getAnalyticsContext } from "../presentation";
import styles from "../analytics.module.css";

export function AnalyticsContextBanner({ report }: { report: ClinicDayDetail }) {
  const context = getAnalyticsContext(report);
  const Icon = context.kind === "sales" || context.kind === "sales_and_refunds" ? BarChart3 : AlertTriangle;

  return (
    <section className={classNames(styles.contextBanner, styles[context.kind])} aria-label="Analytics context">
      <Icon size={20} aria-hidden="true" />
      <div>
        <h2>{context.title}</h2>
        <p>{context.message}</p>
      </div>
    </section>
  );
}

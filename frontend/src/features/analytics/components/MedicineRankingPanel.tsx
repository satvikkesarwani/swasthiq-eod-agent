import type { ReactNode } from "react";

import type { ClinicDayDetail } from "../../../api/types";
import { GlassPanel } from "../../../components/primitives/GlassPanel";
import { formatPaise } from "../../../lib/formatters";
import { quantityUnit } from "../presentation";
import styles from "../analytics.module.css";

export function MedicineRankingPanel({ report }: { report: ClinicDayDetail }) {
  const byQuantity = report.report.analytics.top_medicines_by_quantity;
  const byRevenue = report.report.analytics.top_medicines_by_revenue;

  return (
    <GlassPanel title="Medicine Rankings" description="Ranks are displayed exactly as returned by the backend.">
      <div className={styles.rankingGrid}>
        <RankingList title="By quantity" emptyText="No quantity ranking returned.">
          {byQuantity.map((item) => (
            <li key={`${item.rank}-${item.drug_name}-quantity`}>
              <span className={styles.rankBadge}>#{item.rank}</span>
              <span className={styles.medicineName}>{item.drug_name}</span>
              <span className={styles.rankValue}>{quantityUnit(item.quantity)}</span>
            </li>
          ))}
        </RankingList>
        <RankingList title="By revenue" emptyText="No revenue ranking returned.">
          {byRevenue.map((item) => (
            <li key={`${item.rank}-${item.drug_name}-revenue`}>
              <span className={styles.rankBadge}>#{item.rank}</span>
              <span className={styles.medicineName}>{item.drug_name}</span>
              <span className={styles.rankValue}>{formatPaise(item.revenue_paise)}</span>
            </li>
          ))}
        </RankingList>
      </div>
    </GlassPanel>
  );
}

function RankingList({ title, emptyText, children }: { title: string; emptyText: string; children: ReactNode }) {
  const hasRows = Array.isArray(children) ? children.length > 0 : Boolean(children);
  return (
    <section aria-label={title}>
      <h3>{title}</h3>
      {hasRows ? <ol className={styles.rankingList}>{children}</ol> : <p className={styles.muted}>{emptyText}</p>}
    </section>
  );
}

import type { ClinicDayDetail } from "../../../api/types";
import { StatusPill } from "../../../components/primitives/StatusPill";
import { formatPaise } from "../../../lib/formatters";
import { mapHourlyRevenue } from "../presentation";
import styles from "../analytics.module.css";

export function RevenueByHourTable({ report }: { report: ClinicDayDetail }) {
  const points = mapHourlyRevenue(report);
  if (points.length === 0) {
    return <p className={styles.muted}>No backend hourly rows were returned.</p>;
  }

  return (
    <div className={styles.tableWrap}>
      <table className={styles.table} aria-label="Revenue by hour table">
        <caption>Backend hourly revenue buckets, displayed in response order.</caption>
        <thead>
          <tr>
            <th scope="col">Hour</th>
            <th scope="col">Revenue</th>
            <th scope="col">Peak</th>
          </tr>
        </thead>
        <tbody>
          {points.map((point) => (
            <tr key={point.hourKey}>
              <th scope="row">{point.rangeLabel}</th>
              <td className={styles.moneyCell}>{formatPaise(point.revenuePaise)}</td>
              <td>{point.isPeak ? <StatusPill tone="warning">Backend peak</StatusPill> : <StatusPill tone="neutral">Standard</StatusPill>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

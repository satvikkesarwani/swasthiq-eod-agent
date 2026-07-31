import type { ClinicDayDetail } from "../../../api/types";
import { formatPaise } from "../../../lib/formatters";
import { orderPaymentModes } from "../presentation";
import styles from "../reconciliation.module.css";

export function PaymentModeBreakdown({ report }: { report: ClinicDayDetail }) {
  const rows = orderPaymentModes(report);
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <caption className={styles.caption}>Payment Mode Breakdown</caption>
        <thead>
          <tr>
            <th scope="col">Mode</th>
            <th scope="col">Billed</th>
            <th scope="col">Collected</th>
            <th scope="col">Outstanding</th>
            <th scope="col">Refunds</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ mode, metrics }) => (
            <tr key={mode}>
              <th scope="row" className={styles.modeCell}>{mode}</th>
              <td className={styles.moneyCell}>{formatPaise(metrics.billed_paise)}</td>
              <td className={styles.moneyCell}>{formatPaise(metrics.collected_paise)}</td>
              <td className={styles.moneyCell}>{formatPaise(metrics.outstanding_paise)}</td>
              <td className={styles.moneyCell}>{formatPaise(metrics.refunds_paise)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { ExternalLink } from "lucide-react";

import { Button } from "../../../components/primitives/Button";
import { StatusPill } from "../../../components/primitives/StatusPill";
import { reportRoutes } from "../../../app/routes";
import type { ClinicDaySummary } from "../../../api/types";
import { formatBusinessDate, formatPaise, safeLabel } from "../../../lib/formatters";
import styles from "./RecentReports.module.css";

type RecentReportsListProps = {
  reports: ClinicDaySummary[];
};

export function RecentReportsList({ reports }: RecentReportsListProps) {
  return (
    <ul className={styles.list} aria-label="Recent clinic-day reports">
      {reports.map((report) => (
        <li key={`${report.clinic_id}-${report.business_date}`} className={styles.row}>
          <div>
            <p className={styles.clinic}>{safeLabel(report.clinic_name, report.clinic_id)}</p>
            <p className={styles.meta}>{report.clinic_id} / {formatBusinessDate(report.business_date)}</p>
            <div className={styles.activeFilters}>
              <StatusPill tone={report.rejected_rows > 0 ? "warning" : "healthy"}>{report.status}</StatusPill>
              {report.rejected_rows > 0 && <StatusPill tone="warning">{`${report.rejected_rows} rejected`}</StatusPill>}
            </div>
          </div>
          <div className={styles.moneyGrid}>
            <div><span>Billed</span><strong>{formatPaise(report.total_billed_paise)}</strong></div>
            <div><span>Collected</span><strong>{formatPaise(report.total_collected_paise)}</strong></div>
            <div><span>Outstanding</span><strong>{formatPaise(report.total_outstanding_paise)}</strong></div>
            <div><span>Refunds</span><strong>{formatPaise(report.total_refunds_paise)}</strong></div>
          </div>
          <Button
            to={reportRoutes.reconciliation(report.clinic_id, report.business_date)}
            variant="secondary"
            icon={<ExternalLink size={16} aria-hidden="true" />}
          >
            Open report
          </Button>
        </li>
      ))}
    </ul>
  );
}

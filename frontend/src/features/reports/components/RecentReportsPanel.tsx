import { useNavigation } from "react-router";

import { EmptyState } from "../../../components/feedback/EmptyState";
import { InlineError } from "../../../components/feedback/InlineError";
import { LoadingSkeleton } from "../../../components/feedback/LoadingSkeleton";
import { GlassPanel } from "../../../components/primitives/GlassPanel";
import type { ClinicDayListResponse } from "../../../api/types";
import { RecentReportsFilters } from "./RecentReportsFilters";
import { RecentReportsList } from "./RecentReportsList";
import { ReportsPagination } from "./ReportsPagination";
import type { ReportsQuery } from "../queryParams";
import styles from "./RecentReports.module.css";

export type ReportsLoaderData = {
  query: ReportsQuery;
  response: ClinicDayListResponse | null;
  error: string | null;
};

type RecentReportsPanelProps = {
  data: ReportsLoaderData;
};

export function RecentReportsPanel({ data }: RecentReportsPanelProps) {
  const navigation = useNavigation();
  const loading = navigation.state === "loading";
  const reports = data.response?.items ?? [];
  const hasFilters = Boolean(data.query.clinicId || data.query.dateFrom || data.query.dateTo);

  return (
    <GlassPanel className={styles.panel ?? ""} title="Recent reports" description="Open stored clinic-day reports or filter the backend list.">
      <RecentReportsFilters query={data.query} />
      {data.error && <InlineError message={data.error} />}
      {loading && <LoadingSkeleton rows={4} />}
      {!loading && data.error === null && reports.length === 0 && (
        <EmptyState
          title={hasFilters ? "No reports matched these filters" : "No clinic-day reports yet"}
          message={hasFilters ? "Adjust filters or reset them to see recent reports." : "Import a JSON billing log to create the first report."}
        />
      )}
      {!loading && reports.length > 0 && (
        <>
          <RecentReportsList reports={reports} />
          <ReportsPagination query={data.query} count={reports.length} />
        </>
      )}
    </GlassPanel>
  );
}

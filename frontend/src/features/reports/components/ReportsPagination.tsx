import { useNavigate } from "react-router";

import { Button } from "../../../components/primitives/Button";
import { reportsQueryToSearch, type ReportsQuery } from "../queryParams";
import styles from "./RecentReports.module.css";

type ReportsPaginationProps = {
  query: ReportsQuery;
  count: number;
};

export function ReportsPagination({ query, count }: ReportsPaginationProps) {
  const navigate = useNavigate();
  const previousOffset = Math.max(0, query.offset - query.limit);
  const nextOffset = query.offset + query.limit;
  const canPrevious = query.offset > 0;
  const canNext = count === query.limit;

  const go = (offset: number) => {
    const search = reportsQueryToSearch({ ...query, offset });
    void navigate(search ? `/reports?${search}` : "/reports");
  };

  return (
    <div className={styles.pagination}>
      <span>{count === 0 ? "No reports on this page" : `Showing ${query.offset + 1}-${query.offset + count}`}</span>
      <div className={styles.activeFilters}>
        <Button type="button" variant="ghost" disabled={!canPrevious} onClick={() => go(previousOffset)}>Previous</Button>
        <Button type="button" variant="ghost" disabled={!canNext} onClick={() => go(nextOffset)}>Next</Button>
      </div>
    </div>
  );
}

import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";

import { Button } from "../../../components/primitives/Button";
import { Badge } from "../../../components/primitives/Badge";
import { parseReportsQuery, reportsQueryToSearch, RECENT_REPORTS_LIMIT, type ReportsQuery } from "../queryParams";
import styles from "./RecentReports.module.css";

type RecentReportsFiltersProps = {
  query: ReportsQuery;
};

export function RecentReportsFilters({ query }: RecentReportsFiltersProps) {
  const navigate = useNavigate();
  const [clinicId, setClinicId] = useState(query.clinicId ?? "");
  const [dateFrom, setDateFrom] = useState(query.dateFrom ?? "");
  const [dateTo, setDateTo] = useState(query.dateTo ?? "");

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextQuery = {
      ...(clinicId.trim() ? { clinicId: clinicId.trim() } : {}),
      ...(dateFrom ? { dateFrom } : {}),
      ...(dateTo ? { dateTo } : {}),
      limit: RECENT_REPORTS_LIMIT,
      offset: 0,
    };
    const search = reportsQueryToSearch(nextQuery);
    void navigate(search ? `/reports?${search}` : "/reports");
  };

  const reset = () => {
    setClinicId("");
    setDateFrom("");
    setDateTo("");
    void navigate("/reports");
  };

  const active = parseReportsQuery(`?${reportsQueryToSearch(query)}`);

  return (
    <>
      <form className={styles.filters} onSubmit={submit}>
        <div className={styles.field}>
          <label htmlFor="recent-clinic">Clinic ID</label>
          <input id="recent-clinic" value={clinicId} onChange={(event) => setClinicId(event.target.value)} />
        </div>
        <div className={styles.field}>
          <label htmlFor="recent-from">Date from</label>
          <input id="recent-from" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
        </div>
        <div className={styles.field}>
          <label htmlFor="recent-to">Date to</label>
          <input id="recent-to" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
        </div>
        <div className={styles.filters}>
          <Button type="submit" variant="secondary">Apply filters</Button>
          <Button type="button" variant="ghost" onClick={reset}>Reset</Button>
        </div>
      </form>
      <div className={styles.activeFilters} aria-label="Active filters">
        {active.clinicId && <Badge>Clinic {active.clinicId}</Badge>}
        {active.dateFrom && <Badge>From {active.dateFrom}</Badge>}
        {active.dateTo && <Badge>To {active.dateTo}</Badge>}
      </div>
    </>
  );
}

import { Activity, Wifi } from "lucide-react";
import { Link } from "react-router";

import { useAppContext } from "../../app/AppContext";
import { useReportRouteParams } from "../../lib/routeParams";
import { StatusPill } from "../primitives/StatusPill";
import styles from "./TopBar.module.css";

export function TopBar() {
  const { health, online } = useAppContext();
  const params = useReportRouteParams();
  const contextLabel = params.isValid ? `${params.clinicId} / ${params.businessDate}` : "EOD command centre";

  return (
    <header className={styles.topbar}>
      <Link to="/reports" className={styles.brand} aria-label="SwasthiQ EOD reports home">
        <span className={styles.mark}>SQ</span>
        <span className={styles.brandText}>
          <strong>SwasthiQ EOD</strong>
          <span>{contextLabel}</span>
        </span>
      </Link>
      <div className={styles.statusCluster} aria-label="System status">
        <StatusPill tone={online ? "online" : "unavailable"}>
          {online ? "Network online" : "Network offline"}
        </StatusPill>
        <StatusPill tone={health.state}>
          {health.label}
        </StatusPill>
        <Activity size={18} aria-hidden="true" />
        <Wifi size={18} aria-hidden="true" />
      </div>
    </header>
  );
}

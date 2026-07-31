import { reportRoutes } from "../../app/routes";
import { useReportRouteParams } from "../../lib/routeParams";
import { Badge } from "../primitives/Badge";
import { Button } from "../primitives/Button";
import styles from "./ReportContextBar.module.css";

export function ReportContextBar({ section }: { section: string }) {
  const params = useReportRouteParams();

  if (!params.isValid) {
    return null;
  }

  return (
    <div className={styles.bar} aria-label="Report context">
      <div className={styles.meta}>
        <Badge>Clinic {params.clinicId}</Badge>
        <Badge>{params.businessDate}</Badge>
        <Badge>{section}</Badge>
      </div>
      <Button to={reportRoutes.reports()} variant="ghost" size="small">All reports</Button>
    </div>
  );
}

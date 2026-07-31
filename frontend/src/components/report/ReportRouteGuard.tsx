import type { ReactNode } from "react";

import { reportRoutes } from "../../app/routes";
import { useReportRouteParams } from "../../lib/routeParams";
import { AppErrorState } from "../feedback/AppErrorState";
import { Button } from "../primitives/Button";

export function ReportRouteGuard({ children }: { children: ReactNode }) {
  const params = useReportRouteParams();

  if (!params.isValid) {
    return (
      <AppErrorState
        title="Report context unavailable"
        message="Open a report from the reports workspace so the clinic and business date can be verified."
        action={<Button to={reportRoutes.reports()} variant="primary">Back to reports</Button>}
      />
    );
  }

  return <>{children}</>;
}

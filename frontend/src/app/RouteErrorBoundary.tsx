import { isRouteErrorResponse, Link, useRouteError } from "react-router";

import { AppErrorState } from "../components/feedback/AppErrorState";

export function RouteErrorBoundary() {
  const error = useRouteError();
  const title = isRouteErrorResponse(error) ? "Route unavailable" : "Something went wrong";

  return (
    <main className="standalone-state" aria-labelledby="route-error-title">
      <AppErrorState
        title={title}
        message="The application could not render this view. Internal details have been hidden."
        action={<Link to="/reports">Back to Reports</Link>}
      />
    </main>
  );
}

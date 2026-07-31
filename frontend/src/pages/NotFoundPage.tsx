import { reportRoutes } from "../app/routes";
import { AppErrorState } from "../components/feedback/AppErrorState";
import { Button } from "../components/primitives/Button";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

export function NotFoundPage() {
  useDocumentTitle("Not found");

  return (
    <AppErrorState
      title="Page not found"
      message="The requested workspace route is not available in this frontend foundation."
      action={<Button to={reportRoutes.reports()} variant="primary">Back to reports</Button>}
    />
  );
}

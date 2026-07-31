import { Navigate, createBrowserRouter } from "react-router";

import { AppProviders } from "./AppProviders";
import { RouteErrorBoundary } from "./RouteErrorBoundary";
import { AppShell } from "../components/layout/AppShell";
import { reconciliationLoader } from "../features/reconciliation/loader";
import { reportsLoader } from "../features/reports/loader";
import { AnalyticsPage } from "../pages/AnalyticsPage";
import { NarrativePage } from "../pages/NarrativePage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { ReconciliationPage } from "../pages/ReconciliationPage";
import { ReportsHomePage } from "../pages/ReportsHomePage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: AppProviders,
    ErrorBoundary: RouteErrorBoundary,
    children: [
      { index: true, element: <Navigate to="/reports" replace /> },
      {
        Component: AppShell,
        children: [
          { path: "reports", Component: ReportsHomePage, loader: reportsLoader },
          { path: "reports/:clinicId/:businessDate/reconciliation", Component: ReconciliationPage, loader: reconciliationLoader },
          { path: "reports/:clinicId/:businessDate/analytics", Component: AnalyticsPage },
          { path: "reports/:clinicId/:businessDate/narrative", Component: NarrativePage },
          { path: "*", Component: NotFoundPage },
        ],
      },
    ],
  },
]);

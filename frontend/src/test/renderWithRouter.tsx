import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import type { RouteObject } from "react-router";

import { AppProviders } from "../app/AppProviders";
import { RouteErrorBoundary } from "../app/RouteErrorBoundary";
import { AppShell } from "../components/layout/AppShell";
import { analyticsLoader } from "../features/analytics/loader";
import { reconciliationLoader } from "../features/reconciliation/loader";
import { reportsLoader } from "../features/reports/loader";
import { AnalyticsPage } from "../pages/AnalyticsPage";
import { NarrativePage } from "../pages/NarrativePage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { ReconciliationPage } from "../pages/ReconciliationPage";
import { ReportsHomePage } from "../pages/ReportsHomePage";

export function appRoutes(): RouteObject[] {
  return [
    {
      path: "/",
      Component: AppProviders,
      ErrorBoundary: RouteErrorBoundary,
      children: [
        {
          Component: AppShell,
          children: [
            { path: "reports", Component: ReportsHomePage, loader: reportsLoader },
            { path: "reports/:clinicId/:businessDate/reconciliation", Component: ReconciliationPage, loader: reconciliationLoader },
            { path: "reports/:clinicId/:businessDate/analytics", Component: AnalyticsPage, loader: analyticsLoader },
            { path: "reports/:clinicId/:businessDate/narrative", Component: NarrativePage },
            { path: "*", Component: NotFoundPage },
          ],
        },
      ],
    },
  ];
}

export function renderApp(path = "/reports") {
  const router = createMemoryRouter(appRoutes(), { initialEntries: [path] });
  return {
    router,
    ...render(<RouterProvider router={router} />),
  };
}

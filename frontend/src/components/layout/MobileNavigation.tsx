import { NavLink } from "react-router";

import { reportRoutes } from "../../app/routes";
import { classNames } from "../../lib/classNames";
import { useReportRouteParams } from "../../lib/routeParams";
import { navigationItems } from "./navigationItems";
import styles from "./Navigation.module.css";

function hrefFor(label: string, clinicId: string, businessDate: string): string {
  if (label === "Reconcile") {
    return reportRoutes.reconciliation(clinicId, businessDate);
  }
  if (label === "Analytics") {
    return reportRoutes.analytics(clinicId, businessDate);
  }
  if (label === "Narrative") {
    return reportRoutes.narrative(clinicId, businessDate);
  }
  return reportRoutes.reports();
}

export function MobileNavigation() {
  const params = useReportRouteParams();

  return (
    <nav className={styles.mobileNav} aria-label="Mobile navigation">
      {navigationItems.map((item) => {
        const Icon = item.icon;
        const disabled = item.section === "report-detail" && !params.isValid;
        const to = disabled ? reportRoutes.reports() : hrefFor(item.label, params.clinicId ?? "", params.businessDate ?? "");
        return (
          <NavLink key={item.label} to={to} className={classNames(styles.mobileLink)} aria-disabled={disabled || undefined}>
            <Icon size={18} aria-hidden="true" />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}

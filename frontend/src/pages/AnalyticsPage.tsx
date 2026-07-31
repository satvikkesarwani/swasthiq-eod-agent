import { BarChart3 } from "lucide-react";

import { EmptyState } from "../components/feedback/EmptyState";
import { PageContainer } from "../components/layout/PageContainer";
import { GlassPanel } from "../components/primitives/GlassPanel";
import { StatusPill } from "../components/primitives/StatusPill";
import { ReportContextBar } from "../components/report/ReportContextBar";
import { ReportRouteGuard } from "../components/report/ReportRouteGuard";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import styles from "./Page.module.css";

export function AnalyticsPage() {
  useDocumentTitle("Analytics");

  return (
    <ReportRouteGuard>
      <ReportContextBar section="Analytics" />
      <PageContainer
        eyebrow="Operational analytics"
        title="Analytics"
        description="Reserved space for contract-backed charts and validation cards."
      >
        <div className={styles.twoColumn}>
          <GlassPanel title="Charts" description="Recharts is installed for later contract-backed analytics.">
            <EmptyState
              title="Charts pending data"
              message="The frontend shell includes the chart dependency, but this prompt intentionally avoids rendering made-up values."
            />
          </GlassPanel>
          <GlassPanel title="Runtime" compact>
            <ul className={styles.contractList}>
              <li><span><BarChart3 size={16} aria-hidden="true" /> Chart engine</span><StatusPill tone="healthy">Installed</StatusPill></li>
              <li><span>Financial data</span><StatusPill tone="fallback">Not mocked</StatusPill></li>
            </ul>
          </GlassPanel>
        </div>
      </PageContainer>
    </ReportRouteGuard>
  );
}

import { LoadingSkeleton } from "../components/feedback/LoadingSkeleton";
import { PageContainer } from "../components/layout/PageContainer";
import { ReportContextBar } from "../components/report/ReportContextBar";
import { ReportRouteGuard } from "../components/report/ReportRouteGuard";
import { GlassPanel } from "../components/primitives/GlassPanel";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import styles from "./Page.module.css";

export function ReconciliationPage() {
  useDocumentTitle("Reconciliation");

  return (
    <ReportRouteGuard>
      <ReportContextBar section="Reconciliation" />
      <PageContainer
        eyebrow="Billing review"
        title="Reconciliation"
        description="A guarded placeholder for deterministic billing checks, ingestion issues, and operator review."
      >
        <GlassPanel title="Reconciliation surface" description="Data widgets will mount here after the dedicated report workflow prompt.">
          <div className={styles.stack}>
            <p className={styles.copy}>No clinic totals or variance figures are fabricated in the foundation build.</p>
            <LoadingSkeleton rows={3} />
          </div>
        </GlassPanel>
      </PageContainer>
    </ReportRouteGuard>
  );
}

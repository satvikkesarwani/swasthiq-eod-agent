import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useLoaderData } from "react-router";

import { GlassPanel } from "../components/primitives/GlassPanel";
import { StatusPill } from "../components/primitives/StatusPill";
import { PageContainer } from "../components/layout/PageContainer";
import { BillingImportForm } from "../features/import/components/BillingImportForm";
import { ImportPipelineStatus } from "../features/import/components/ImportPipelineStatus";
import { ValidationIssuesDrawer } from "../features/import/components/ValidationIssuesDrawer";
import type { ImportResult } from "../features/import/types";
import { RecentReportsPanel, type ReportsLoaderData } from "../features/reports/components/RecentReportsPanel";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import styles from "./Page.module.css";

export function ReportsHomePage() {
  useDocumentTitle("Reports");
  const loaderData: ReportsLoaderData = useLoaderData();
  const [partialResult, setPartialResult] = useState<ImportResult | null>(null);
  const [issuesOpen, setIssuesOpen] = useState(false);

  return (
    <PageContainer
      eyebrow="Reports workspace"
      title="Reports"
      description="Import a clinic-day billing log, review backend validation outcomes, and open stored EOD reports."
    >
      <div className={styles.twoColumn}>
        <BillingImportForm
          recentReports={loaderData.response?.items ?? []}
          onPartialResult={setPartialResult}
          onReviewIssues={() => setIssuesOpen(true)}
        />
        <GlassPanel title="Pipeline status" description="The browser checks file structure; the backend validates rows and owns every report value.">
          <ImportPipelineStatus
            status={partialResult ? "completed_with_errors" : "idle"}
            hasFile={Boolean(partialResult)}
            hasResult={Boolean(partialResult)}
            rejectedRows={partialResult?.rejectedRows ?? 0}
          />
          <div className={styles.contractList}>
            <div className={styles.contractNote}>
              <ShieldCheck size={18} aria-hidden="true" />
              <span>Rows are validated securely by the billing service after submission.</span>
            </div>
            <div className={styles.contractPills}>
              <StatusPill tone="healthy">Native fetch</StatusPill>
              <StatusPill tone="fallback">Narrative later</StatusPill>
            </div>
          </div>
        </GlassPanel>
      </div>
      <RecentReportsPanel data={loaderData} />
      <ValidationIssuesDrawer open={issuesOpen} result={partialResult} onClose={() => setIssuesOpen(false)} />
    </PageContainer>
  );
}

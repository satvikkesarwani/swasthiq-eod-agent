import { Search } from "lucide-react";

import { EmptyState } from "../components/feedback/EmptyState";
import { Button } from "../components/primitives/Button";
import { GlassPanel } from "../components/primitives/GlassPanel";
import { StatusPill } from "../components/primitives/StatusPill";
import { PageContainer } from "../components/layout/PageContainer";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import styles from "./Page.module.css";

export function ReportsHomePage() {
  useDocumentTitle("Reports");

  return (
    <PageContainer
      eyebrow="Reports workspace"
      title="Grounded EOD reports"
      description="Review imported clinic days, then open reconciliation, analytics, or narrative views when a report context is available."
    >
      <div className={styles.twoColumn}>
        <GlassPanel title="Report finder" description="The foundation is connected to the backend contract without rendering synthetic report values.">
          <EmptyState
            title="No report selected"
            message="Prompt 5 establishes the shell and typed API surface. Report listing and import workflows remain reserved for later prompts."
            action={(
              <div className={styles.actions}>
                <Button variant="primary" icon={<Search size={16} aria-hidden="true" />}>Ready for API data</Button>
              </div>
            )}
          />
        </GlassPanel>
        <GlassPanel title="Contract readiness" compact>
          <ul className={styles.contractList}>
            <li><span>OpenAPI schema</span><StatusPill tone="healthy">Generated</StatusPill></li>
            <li><span>Native fetch client</span><StatusPill tone="healthy">Ready</StatusPill></li>
            <li><span>Business pages</span><StatusPill tone="fallback">Placeholder</StatusPill></li>
          </ul>
        </GlassPanel>
      </div>
    </PageContainer>
  );
}

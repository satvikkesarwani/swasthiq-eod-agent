import { FileText } from "lucide-react";

import { EmptyState } from "../components/feedback/EmptyState";
import { PageContainer } from "../components/layout/PageContainer";
import { GlassPanel } from "../components/primitives/GlassPanel";
import { StatusPill } from "../components/primitives/StatusPill";
import { ReportContextBar } from "../components/report/ReportContextBar";
import { ReportRouteGuard } from "../components/report/ReportRouteGuard";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import styles from "./Page.module.css";

export function NarrativePage() {
  useDocumentTitle("Narrative");

  return (
    <ReportRouteGuard>
      <ReportContextBar section="Narrative" />
      <PageContainer
        eyebrow="Grounded narrative"
        title="Narrative"
        description="A protected placeholder for the backend narrative endpoint, citations, and fallback labels."
      >
        <div className={styles.twoColumn}>
          <GlassPanel title="Narrative panel" description="Prompt 4's grounded narrative contract is available through the generated API client.">
            <EmptyState
              title="Narrative not generated"
              message="Generation controls and grounded citation rendering belong to a later prompt."
            />
          </GlassPanel>
          <GlassPanel title="AI status" compact>
            <ul className={styles.contractList}>
              <li><span><FileText size={16} aria-hidden="true" /> Endpoint type</span><StatusPill tone="ai">Typed</StatusPill></li>
              <li><span>Fallback display</span><StatusPill tone="fallback">Supported</StatusPill></li>
            </ul>
          </GlassPanel>
        </div>
      </PageContainer>
    </ReportRouteGuard>
  );
}

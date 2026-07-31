import { useMemo, useState } from "react";
import { useLoaderData, useNavigation } from "react-router";

import { ApiError } from "../api/client";
import type { NarrativeResponse } from "../api/types";
import { analyticsPath, reconciliationPath, reportRoutes } from "../app/routes";
import { PageContainer } from "../components/layout/PageContainer";
import { Button } from "../components/primitives/Button";
import { GlassPanel } from "../components/primitives/GlassPanel";
import { copyTextToClipboard } from "../features/narrative/clipboard";
import { GenerationDetailsPanel } from "../features/narrative/components/GenerationDetailsPanel";
import { NarrativeControls } from "../features/narrative/components/NarrativeControls";
import { NarrativeHeader } from "../features/narrative/components/NarrativeHeader";
import { NarrativeLoadError, NarrativeNotFound } from "../features/narrative/components/NarrativeErrorState";
import { NarrativeSkeleton } from "../features/narrative/components/NarrativeSkeleton";
import { NarrativeStatusBanner } from "../features/narrative/components/NarrativeStatusBanner";
import { NarrativeSummaryPanel } from "../features/narrative/components/NarrativeSummaryPanel";
import { TracedFiguresPanel } from "../features/narrative/components/TracedFiguresPanel";
import { UnavailableMetricsPanel } from "../features/narrative/components/UnavailableMetricsPanel";
import { requestNarrativeGeneration } from "../features/narrative/actions";
import { copySummaryText } from "../features/narrative/presentation";
import type { NarrativeLoaderData, NarrativeMutationState } from "../features/narrative/types";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import styles from "../features/narrative/narrative.module.css";

export function NarrativePage() {
  const loaderData = useLoaderData<NarrativeLoaderData>();
  const navigation = useNavigation();
  const online = useOnlineStatus();
  const [localNarrative, setLocalNarrative] = useState<{ source: "cached" | "generated"; narrative: NarrativeResponse } | null>(null);
  const [mutation, setMutation] = useState<NarrativeMutationState>({ state: "idle", error: null, requestId: null });
  const [copyStatus, setCopyStatus] = useState("");

  const report = loaderData.state === "ready" ? loaderData.report : null;
  const loadedNarrative = loaderData.state === "ready" && loaderData.narrative.state === "available" ? loaderData.narrative : null;
  const visibleNarrative = localNarrative ?? loadedNarrative;
  const narrative = visibleNarrative?.narrative ?? null;
  const narrativeSource = visibleNarrative?.source ?? null;

  useDocumentTitle(loaderData.state === "ready" ? "AI Narrative Summary" : "Narrative unavailable");

  const controls = useMemo(() => {
    if (!report) {
      return null;
    }
    const onGenerate = (forceRegenerate: boolean) => {
      if (mutation.state === "generating") {
        return;
      }
      if (forceRegenerate && narrative && !window.confirm("This creates a new summary from the same deterministic report.")) {
        return;
      }
      setMutation({ state: "generating", forceRegenerate, error: null, requestId: null });
      requestNarrativeGeneration(report.clinic_id, report.business_date, forceRegenerate)
        .then((nextNarrative) => {
          setLocalNarrative({ source: "generated", narrative: nextNarrative });
          setMutation({ state: "idle", error: null, requestId: null });
        })
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") {
            return;
          }
          const requestId = error instanceof ApiError ? error.requestId : null;
          const message = error instanceof ApiError && error.status === 429
            ? "Summary generation is temporarily rate limited. Please wait before retrying."
            : "The summary could not be generated. Existing summary content was kept.";
          setMutation({ state: "failed", error: message, requestId });
        });
    };
    return <NarrativeControls narrative={narrative} mutation={mutation} online={online} onGenerate={onGenerate} />;
  }, [mutation, narrative, online, report]);

  async function handleCopy() {
    if (!report || !narrative) {
      return;
    }
    setCopyStatus("");
    try {
      await copyTextToClipboard(copySummaryText(report, narrative));
      setCopyStatus("Summary copied.");
    } catch {
      setCopyStatus("Copy failed. Select and copy the summary manually.");
    }
  }

  if (navigation.state === "loading" && loaderData.state !== "ready") {
    return <NarrativeSkeleton />;
  }

  if (loaderData.state === "not_found") {
    return (
      <PageContainer eyebrow="Grounded narrative" title="Report not found" description="Import a billing log to create this clinic-day report.">
        <NarrativeNotFound data={loaderData} />
      </PageContainer>
    );
  }

  if (loaderData.state === "error") {
    return (
      <PageContainer eyebrow="Grounded narrative" title="Narrative unavailable" description="The application shell is still available.">
        <NarrativeLoadError data={loaderData} />
      </PageContainer>
    );
  }

  if (!report) {
    return null;
  }

  const narrativeLoadError = loaderData.narrative.state === "error" ? loaderData.narrative : null;

  return (
    <div className={styles.page} aria-busy={mutation.state === "generating" || navigation.state === "loading" ? "true" : undefined}>
      <NarrativeHeader report={report} narrative={narrative} source={narrativeSource} />
      <NarrativeStatusBanner report={report} narrative={narrative} />
      {narrativeLoadError && (
        <section className={`${styles.statusBanner} ${styles.error}`} role="alert">
          <div>
            <h2>{narrativeLoadError.title}</h2>
            <p>{narrativeLoadError.message}</p>
            {narrativeLoadError.requestId && <p>Support request ID: {narrativeLoadError.requestId}</p>}
          </div>
        </section>
      )}
      <div className={styles.mainGrid}>
        <GlassPanel title="Owner Summary" description="Plain-language text ready for the clinic owner.">
          <NarrativeSummaryPanel report={report} narrative={narrative} source={narrativeSource} mutation={mutation} copyStatus={copyStatus} onCopy={() => void handleCopy()} controls={controls} />
        </GlassPanel>
        <GlassPanel title="Narrative Control" description="Generation runs on the backend and never exposes provider keys to the browser.">
          {controls}
          <p className={styles.muted}>Opening this page never auto-generates a summary. The button makes one explicit backend request.</p>
          {mutation.state === "failed" && mutation.requestId && <p className={styles.supportDetails}>Support request ID: <code>{mutation.requestId}</code></p>}
        </GlassPanel>
      </div>
      <div className={styles.supportGrid}>
        <GlassPanel title="Traced Figures" description="Backend-provided proof that narrative figures map to deterministic report fields.">
          <TracedFiguresPanel narrative={narrative} />
        </GlassPanel>
        <GlassPanel title="Unavailable Metrics" description="Metrics that cannot be computed from the billing log are shown plainly.">
          <UnavailableMetricsPanel narrative={narrative} />
        </GlassPanel>
      </div>
      <GlassPanel title="Generation Details" description="Safe metadata only. No prompts, raw model output, keys or billing rows are shown.">
        <GenerationDetailsPanel report={report} narrative={narrative} source={narrativeSource} />
      </GlassPanel>
      <nav className={styles.bottomNav} aria-label="Continue exploring report">
        <Button to={reconciliationPath(report.clinic_id, report.business_date)} variant="primary">View Reconciliation</Button>
        <Button to={analyticsPath(report.clinic_id, report.business_date)} variant="secondary">View Analytics</Button>
        <Button to={reportRoutes.reports()} variant="ghost">Back to Reports</Button>
      </nav>
    </div>
  );
}

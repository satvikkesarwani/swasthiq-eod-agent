import { RefreshCw, Sparkles } from "lucide-react";

import type { NarrativeResponse } from "../../../api/types";
import { Button } from "../../../components/primitives/Button";
import type { NarrativeMutationState } from "../types";
import styles from "../narrative.module.css";

type NarrativeControlsProps = {
  narrative: NarrativeResponse | null;
  mutation: NarrativeMutationState;
  online: boolean;
  onGenerate: (forceRegenerate: boolean) => void;
};

export function NarrativeControls({ narrative, mutation, online, onGenerate }: NarrativeControlsProps) {
  const isWorking = mutation.state === "generating";
  const hasNarrative = narrative !== null;

  return (
    <div className={styles.buttonRow} aria-busy={isWorking || undefined}>
      <Button
        type="button"
        variant="primary"
        loading={isWorking && !mutation.forceRegenerate}
        disabled={isWorking || !online}
        icon={<Sparkles size={16} aria-hidden="true" />}
        onClick={() => onGenerate(false)}
      >
        {hasNarrative ? "Use Cached Summary" : "Generate Summary"}
      </Button>
      {hasNarrative && (
        <Button
          type="button"
          variant="secondary"
          loading={isWorking && mutation.forceRegenerate}
          disabled={isWorking || !online}
          icon={<RefreshCw size={16} aria-hidden="true" />}
          onClick={() => onGenerate(true)}
        >
          Regenerate Summary
        </Button>
      )}
      {!online && <p className={styles.muted}>Reconnect before generating a summary.</p>}
    </div>
  );
}

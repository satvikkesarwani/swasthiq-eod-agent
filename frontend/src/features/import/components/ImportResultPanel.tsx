import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Button } from "../../../components/primitives/Button";
import { StatusPill } from "../../../components/primitives/StatusPill";
import { reportRoutes } from "../../../app/routes";
import { classNames } from "../../../lib/classNames";
import type { ImportResult } from "../types";
import styles from "./ImportWorkflow.module.css";

type ImportResultPanelProps = {
  result: ImportResult;
  onReviewIssues: () => void;
  onImportAnother: () => void;
};

export function ImportResultPanel({ result, onReviewIssues, onImportAnother }: ImportResultPanelProps) {
  const partial = result.rejectedRows > 0;
  return (
    <section className={classNames(styles.result, partial && styles.warning)} tabIndex={-1} aria-live="polite">
      <div className={styles.actions}>
        {partial ? <AlertTriangle size={22} aria-hidden="true" /> : <CheckCircle2 size={22} aria-hidden="true" />}
        <div>
          <h2>{partial ? "Report generated with validation issues" : "Billing log processed successfully"}</h2>
          <p className={styles.hint}>
            {partial
              ? "Report generated from accepted rows. Some rows were excluded because they did not match the billing schema."
              : result.operation === "unchanged"
                ? "The submitted report matches the existing deterministic output."
                : "Opening the EOD report after the recent reports list refreshes."}
          </p>
        </div>
      </div>
      <div className={styles.resultGrid}>
        <div><span>Operation</span><strong>{result.operation}</strong></div>
        <div><span>Status</span><strong><StatusPill tone={partial ? "warning" : "healthy"}>{result.status}</StatusPill></strong></div>
        <div><span>Received rows</span><strong>{result.receivedRows}</strong></div>
        <div><span>Accepted rows</span><strong>{result.acceptedRows}</strong></div>
        <div><span>Rejected rows</span><strong>{result.rejectedRows}</strong></div>
        <div><span>Report hash</span><strong>{result.reportHash.slice(0, 18)}...</strong></div>
      </div>
      {result.warnings.length > 0 && (
        <div>
          <strong>Backend warnings</strong>
          <ul>
            {result.warnings.map((warning) => <li key={warning}>{warning}</li>)}
          </ul>
        </div>
      )}
      <div className={styles.actions}>
        {partial && <Button type="button" variant="secondary" onClick={onReviewIssues}>Review issues</Button>}
        <Button to={reportRoutes.reconciliation(result.clinicId, result.businessDate)} variant="primary">Continue to reconciliation</Button>
        <Button type="button" variant="ghost" onClick={onImportAnother}>Import another file</Button>
      </div>
    </section>
  );
}

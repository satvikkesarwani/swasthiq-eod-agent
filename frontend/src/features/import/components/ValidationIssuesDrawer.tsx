import { useCallback, useEffect, useState } from "react";

import { getClinicDayErrors } from "../../../api/endpoints";
import { Drawer } from "../../../components/primitives/Drawer";
import { Button } from "../../../components/primitives/Button";
import { Badge } from "../../../components/primitives/Badge";
import { InlineError } from "../../../components/feedback/InlineError";
import { LoadingSkeleton } from "../../../components/feedback/LoadingSkeleton";
import { reportRoutes } from "../../../app/routes";
import type { ImportResult, SafeIssue } from "../types";
import styles from "./ImportWorkflow.module.css";

const ISSUE_LIMIT = 20;

type ValidationIssuesDrawerProps = {
  open: boolean;
  result: ImportResult | null;
  onClose: () => void;
};

export function ValidationIssuesDrawer({ open, result, onClose }: ValidationIssuesDrawerProps) {
  const [issues, setIssues] = useState<SafeIssue[]>([]);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  const loadIssues = useCallback(async (nextOffset: number, append: boolean) => {
    if (!result) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await getClinicDayErrors(result.clinicId, result.businessDate, { limit: ISSUE_LIMIT, offset: nextOffset });
      setIssues((current) => {
        const merged = append ? [...current] : [];
        const seen = new Set(merged.map((issue) => `${issue.row_index}:${issue.field_path ?? ""}:${issue.error_code}:${issue.message}`));
        for (const issue of response.errors) {
          const key = `${issue.row_index}:${issue.field_path ?? ""}:${issue.error_code}:${issue.message}`;
          if (!seen.has(key)) {
            merged.push(issue);
          }
        }
        return merged;
      });
      setOffset(response.offset + response.errors.length);
      setHasMore(response.errors.length === response.limit);
    } catch {
      setError("Validation issues could not be loaded. Try again.");
    } finally {
      setLoading(false);
    }
  }, [result]);

  useEffect(() => {
    if (open && result) {
      setIssues([]);
      setOffset(0);
      setHasMore(false);
      void loadIssues(0, false);
    }
  }, [loadIssues, open, result]);

  return (
    <Drawer open={open} title="Validation issues" onClose={onClose}>
      {result && (
        <div className={styles.fileCard}>
          <div className={styles.metaGrid}>
            <div><span>Clinic</span><strong>{result.clinicId}</strong></div>
            <div><span>Date</span><strong>{result.businessDate}</strong></div>
            <div><span>Rejected rows</span><strong>{result.rejectedRows}</strong></div>
            <div><span>Status</span><strong>{result.status}</strong></div>
          </div>
        </div>
      )}
      {loading && issues.length === 0 && <LoadingSkeleton rows={4} />}
      {error && <InlineError message={error} />}
      <ul className={styles.issueList}>
        {issues.map((issue) => (
          <li key={`${issue.row_index}-${issue.field_path ?? "row"}-${issue.error_code}-${issue.message}`}>
            <div className={styles.actions}>
              <Badge>Row {issue.row_index + 1}</Badge>
              <Badge>{issue.error_code}</Badge>
            </div>
            <p>{issue.message}</p>
            <p>{issue.field_path ? `Field: ${issue.field_path}` : "Field: row"}</p>
            {issue.visit_id && <p>Visit ID: {issue.visit_id}</p>}
          </li>
        ))}
      </ul>
      <div className={styles.actions}>
        {hasMore && <Button type="button" variant="secondary" onClick={() => void loadIssues(offset, true)} loading={loading}>Load more</Button>}
        {error && <Button type="button" variant="secondary" onClick={() => void loadIssues(offset, false)}>Retry</Button>}
        {result && <Button to={reportRoutes.reconciliation(result.clinicId, result.businessDate)} variant="primary">Continue to report</Button>}
      </div>
    </Drawer>
  );
}

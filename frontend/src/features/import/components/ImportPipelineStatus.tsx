import { StatusPill } from "../../../components/primitives/StatusPill";
import type { ImportStatus } from "../types";
import styles from "./ImportWorkflow.module.css";

type ImportPipelineStatusProps = {
  status: ImportStatus;
  hasFile: boolean;
  hasResult: boolean;
  rejectedRows: number;
};

export function ImportPipelineStatus({ status, hasFile, hasResult, rejectedRows }: ImportPipelineStatusProps) {
  return (
    <ul className={styles.pipeline}>
      <li><span>JSON selected</span><StatusPill tone={hasFile ? "healthy" : status === "reading_file" ? "checking" : "neutral"}>{status === "reading_file" ? "Reading" : hasFile ? "Ready" : "Waiting"}</StatusPill></li>
      <li><span>Backend validation</span><StatusPill tone={hasResult ? rejectedRows > 0 ? "warning" : "healthy" : "neutral"}>{hasResult ? "Complete" : "After submit"}</StatusPill></li>
      <li><span>EOD report generated</span><StatusPill tone={hasResult ? "healthy" : "neutral"}>{hasResult ? "Stored" : "Pending"}</StatusPill></li>
      <li><span>AI summary</span><StatusPill tone="fallback">Available later</StatusPill></li>
    </ul>
  );
}

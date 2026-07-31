import { classNames } from "../../lib/classNames";
import styles from "./StatusPill.module.css";

export type StatusTone = "neutral" | "checking" | "healthy" | "online" | "degraded" | "warning" | "unavailable" | "error" | "ai" | "fallback";

type StatusPillProps = {
  tone?: StatusTone;
  children: string;
};

export function StatusPill({ tone = "neutral", children }: StatusPillProps) {
  return (
    <span className={classNames(styles.pill, styles[tone])}>
      <span className={styles.dot} aria-hidden="true" />
      {children}
    </span>
  );
}

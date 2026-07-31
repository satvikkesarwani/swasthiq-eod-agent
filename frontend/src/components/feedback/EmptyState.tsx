import type { ReactNode } from "react";

import styles from "./Feedback.module.css";

type EmptyStateProps = {
  title: string;
  message: string;
  action?: ReactNode;
};

export function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className={styles.state}>
      <div>
        <h2>{title}</h2>
        <p>{message}</p>
        {action}
      </div>
    </div>
  );
}

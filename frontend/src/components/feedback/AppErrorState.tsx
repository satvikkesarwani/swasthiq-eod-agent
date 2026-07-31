import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";

import styles from "./Feedback.module.css";

type AppErrorStateProps = {
  title: string;
  message: string;
  action?: ReactNode;
};

export function AppErrorState({ title, message, action }: AppErrorStateProps) {
  return (
    <div className={styles.state} role="alert">
      <div>
        <AlertTriangle size={28} aria-hidden="true" />
        <h2>{title}</h2>
        <p>{message}</p>
        {action}
      </div>
    </div>
  );
}

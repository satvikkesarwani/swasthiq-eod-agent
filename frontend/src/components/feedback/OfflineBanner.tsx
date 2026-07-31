import { WifiOff } from "lucide-react";

import styles from "./Feedback.module.css";

export function OfflineBanner({ online }: { online: boolean }) {
  if (online) {
    return null;
  }

  return (
    <div className={styles.banner} role="status">
      <WifiOff size={18} aria-hidden="true" />
      <span>Network connection unavailable</span>
    </div>
  );
}

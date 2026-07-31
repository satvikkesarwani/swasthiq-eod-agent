import styles from "./Feedback.module.css";

type Toast = {
  id: string;
  message: string;
};

type ToastRegionProps = {
  toasts: Toast[];
};

export function ToastRegion({ toasts }: ToastRegionProps) {
  return (
    <div className={styles.toastRegion} role="status" aria-live="polite" aria-atomic="false">
      {toasts.map((toast) => (
        <div key={toast.id} className={styles.toast}>
          <p>{toast.message}</p>
        </div>
      ))}
    </div>
  );
}

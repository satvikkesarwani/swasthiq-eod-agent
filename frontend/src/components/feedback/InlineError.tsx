import styles from "./Feedback.module.css";

export function InlineError({ message }: { message: string }) {
  return <p className={styles.inlineError}>{message}</p>;
}

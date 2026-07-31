import type { ReactNode } from "react";

import styles from "./Layout.module.css";

type PageContainerProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
};

export function PageContainer({ eyebrow, title, description, children }: PageContainerProps) {
  return (
    <>
      <div className={styles.pageHeader}>
        <p className={styles.eyebrow}>{eyebrow}</p>
        <h1 className={styles.title}>{title}</h1>
        <p className={styles.description}>{description}</p>
      </div>
      {children}
    </>
  );
}

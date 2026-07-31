import type { ElementType, ReactNode } from "react";

import { classNames } from "../../lib/classNames";
import styles from "./GlassPanel.module.css";

type GlassPanelProps = {
  as?: ElementType;
  title?: string;
  description?: string;
  actions?: ReactNode;
  compact?: boolean;
  className?: string;
  children: ReactNode;
};

export function GlassPanel({ as: Component = "section", title, description, actions, compact = false, className, children }: GlassPanelProps) {
  return (
    <Component className={classNames(styles.panel, compact && styles.compact, className)}>
      {(title || description || actions) && (
        <div className={styles.header}>
          <div>
            {title && <h2 className={styles.title}>{title}</h2>}
            {description && <p className={styles.description}>{description}</p>}
          </div>
          {actions}
        </div>
      )}
      {children}
    </Component>
  );
}

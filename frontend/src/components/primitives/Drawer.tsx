import { X } from "lucide-react";
import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { IconButton } from "./IconButton";
import styles from "./Drawer.module.css";

type DrawerProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
};

export function Drawer({ open, title, onClose, children }: DrawerProps) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const restoreFocusRef = useRef<Element | null>(null);

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    restoreFocusRef.current = document.activeElement;
    closeRef.current?.focus();
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", onKeyDown);
      if (restoreFocusRef.current instanceof HTMLElement) {
        restoreFocusRef.current.focus();
      }
    };
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  const mount = document.getElementById("overlay-root") ?? document.body;
  return createPortal(
    <>
      <button className={styles.backdrop} type="button" aria-label="Close drawer" onClick={onClose} />
      <aside className={styles.drawer} role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <div className={styles.header}>
          <h2 id={titleId} className={styles.title}>{title}</h2>
          <IconButton ref={closeRef} label="Close drawer" onClick={onClose}>
            <X size={18} aria-hidden="true" />
          </IconButton>
        </div>
        {children}
      </aside>
    </>,
    mount,
  );
}

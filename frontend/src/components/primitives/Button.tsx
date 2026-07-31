import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link, type LinkProps } from "react-router";

import { classNames } from "../../lib/classNames";
import styles from "./Button.module.css";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

type SharedProps = {
  variant?: ButtonVariant;
  size?: "default" | "small";
  loading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
};

type NativeButtonProps = SharedProps & ButtonHTMLAttributes<HTMLButtonElement> & { to?: never };
type LinkButtonProps = SharedProps & { to: LinkProps["to"] };

export type ButtonProps = NativeButtonProps | LinkButtonProps;

export function Button(props: ButtonProps) {
  const { variant = "secondary", size = "default", loading = false, icon, children } = props;
  const className = classNames(styles.button, styles[variant], size === "small" && styles.small);
  const content = (
    <>
      {loading ? <span className={styles.spinner} aria-hidden="true" /> : icon}
      <span>{children}</span>
    </>
  );

  if ("to" in props && props.to !== undefined) {
    return (
      <Link to={props.to} className={className} aria-disabled={loading || undefined}>
        {content}
      </Link>
    );
  }

  const { type = "button", disabled, onClick } = props;
  return (
    <button type={type} disabled={disabled || loading} onClick={onClick} className={className} aria-busy={loading || undefined}>
      {content}
    </button>
  );
}

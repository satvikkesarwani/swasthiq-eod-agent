import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";

import { classNames } from "../../lib/classNames";
import buttonStyles from "./Button.module.css";

type IconButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children" | "aria-label"> & {
  label: string;
  children: ReactNode;
  variant?: "secondary" | "ghost";
};

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  { label, children, variant = "ghost", className, type = "button", ...rest },
  ref,
) {
  return (
    <button
      {...rest}
      ref={ref}
      type={type}
      aria-label={label}
      className={classNames(buttonStyles.button, buttonStyles.iconOnly, buttonStyles[variant], className)}
    >
      {children}
    </button>
  );
});

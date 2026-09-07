import type { ButtonHTMLAttributes } from "react";

type Variant = "default" | "primary" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const variantClass: Record<Variant, string> = {
  default: "btn",
  primary: "btn btn-primary",
  danger: "btn btn-danger",
};

export function Button({ variant = "default", className, ...rest }: ButtonProps) {
  const classes = [variantClass[variant], className].filter(Boolean).join(" ");
  return <button className={classes} {...rest} />;
}

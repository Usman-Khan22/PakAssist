import { ArrowRight } from "lucide-react";
import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
  icon?: boolean;
};

export default function Button({
  children,
  variant = "primary",
  icon = false,
  type = "button",
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button {...props} type={type} className={`${variant}-button ${className}`.trim()}>
      {children}
      {icon && <ArrowRight size={16} aria-hidden="true" />}
    </button>
  );
}

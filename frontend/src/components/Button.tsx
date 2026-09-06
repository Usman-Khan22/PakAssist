import { ArrowRight } from "lucide-react";

export default function Button({
  children,
  variant = "primary",
  onClick,
  icon = true,
  type = "button",
}: {
  children: React.ReactNode;
  variant?: "primary" | "outline" | "quiet";
  onClick?: () => void;
  icon?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <button type={type} onClick={onClick} className={`btn btn-${variant}`}>
      {children}
      {icon && <ArrowRight size={16} />}
    </button>
  );
}

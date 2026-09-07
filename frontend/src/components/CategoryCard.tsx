import type { LocalizedText } from "../translations";
import { useLanguage } from "../language";
import { useNavigate } from "react-router-dom";
import { ArrowRight, BookOpen, CalendarDays, CreditCard, FileText, Landmark, ShieldCheck } from "lucide-react";

export default function CategoryCard({ item }: { item: [LocalizedText, LocalizedText, string] }) {
  const { localize } = useLanguage();
  const navigate = useNavigate();
  const icons: Record<string, typeof FileText> = {
    Passport: BookOpen,
    "CNIC/NADRA": CreditCard,
    "Driving License": CalendarDays,
    "Vehicle Registration": FileText,
    "Tax & Revenue": ShieldCheck,
    Documents: Landmark,
  };
  const Icon = icons[item[2]] || FileText;
  return (
    <button
      className="category-card"
      onClick={() =>
        navigate(`/services?category=${encodeURIComponent(item[2])}`)
      }
    >
      <span className="icon-tile">
        <Icon size={19} />
      </span>
      <span>
        <b>{localize(item[0])}</b>
        <small>{localize(item[1])}</small>
      </span>
      <ArrowRight size={17} />
    </button>
  );
}

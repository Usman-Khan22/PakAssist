import { categoryLabels } from "../data";
import { useLanguage } from "../language";
import { Link } from "react-router-dom";
import { ArrowRight, BookOpen, CalendarDays, CreditCard, FileText, Landmark, ShieldCheck } from "lucide-react";
import { type Service } from "../data";

export default function ServiceCard({ service }: { service: Service }) {
  const { t, language, localize } = useLanguage();
  const icons: Record<string, typeof FileText> = {
    Passport: BookOpen,
    "CNIC/NADRA": CreditCard,
    "Driving License": CalendarDays,
    "Vehicle Registration": FileText,
    "Tax & Revenue": ShieldCheck,
    Documents: Landmark,
  };
  const Icon = icons[service.category] || FileText;
  return (
    <Link to={`/services/${service.slug}`} className="service-card">
      <div className="service-card-top">
        <span className="icon-tile">
          <Icon size={19} />
        </span>
        <span className="badge available"> {t.available} </span>
      </div>
      <small>{localize(categoryLabels[service.category])}</small>
      <h3>{localize(service.title[language])}</h3>
      <p>{localize(service.description[language])}</p>
      <span className="card-link"> {t.viewGuide} <ArrowRight size={15} />
      </span>
    </Link>
  );
}

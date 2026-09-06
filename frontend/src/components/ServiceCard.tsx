import { Link } from "react-router-dom";
import { ArrowRight, BookOpen, CalendarDays, CreditCard, FileText, Landmark, ShieldCheck } from "lucide-react";
import { type Service } from "../data";

export default function ServiceCard({ service }: { service: Service }) {
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
        <span className="badge available">Available</span>
      </div>
      <small>{service.category}</small>
      <h3>{service.title}</h3>
      <p>{service.description}</p>
      <span className="card-link">
        View guide <ArrowRight size={15} />
      </span>
    </Link>
  );
}

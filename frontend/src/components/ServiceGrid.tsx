import { type Service } from "../data";
import CategoryCard from "./CategoryCard";
import ServiceCard from "./ServiceCard";

const categoryData = [
  [
    "Passport Services",
    "Your passport journey, clearly explained.",
    "Passport",
  ],
  ["CNIC / NADRA", "Identity services without the confusion.", "CNIC/NADRA"],
  ["Driving License", "From learner permit to renewal.", "Driving License"],
  [
    "Vehicle Registration",
    "Transfer, tax and registration guidance.",
    "Vehicle Registration",
  ],
  [
    "Tax & FBR Assistance",
    "Understand filing without the jargon.",
    "Tax & Revenue",
  ],
  [
    "Domicile & Certificates",
    "The documents your next step needs.",
    "Documents",
  ],
];

export default function ServiceGrid({ services }: { services?: Service[] }) {
  return services ? (
    <div className="service-grid">
      {services.map((service) => <ServiceCard key={service.slug} service={service} />)}
    </div>
  ) : (
    <div className="category-grid">
      {categoryData.map((item) => <CategoryCard key={item[0]} item={item} />)}
    </div>
  );
}

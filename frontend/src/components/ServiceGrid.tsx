import { copy, type LocalizedText } from "../translations";
import { type Service } from "../data";
import CategoryCard from "./CategoryCard";
import ServiceCard from "./ServiceCard";

const categoryData: [LocalizedText, LocalizedText, string][] = [
  [
    copy.passportServices,
    copy.yourPassportJourneyClearlyExplained,
    copy.passport.en,
  ],
  [copy.cnicNadra, copy.identityServicesWithoutTheConfusion, copy.cnicnadra.en],
  [copy.drivingLicense, copy.fromLearnerPermitToRenewal, copy.drivingLicense.en],
  [
    copy.vehicleRegistration,
    copy.transferTaxAndRegistrationGuidance,
    copy.vehicleRegistration.en,
  ],
  [
    copy.taxFbrAssistance,
    copy.understandFilingWithoutTheJargon,
    copy.taxRevenue.en,
  ],
  [
    copy.domicileCertificates,
    copy.theDocumentsYourNextStepNeeds,
    copy.documents.en,
  ],
];

export default function ServiceGrid({ services }: { services?: Service[] }) {
  return services ? (
    <div className="service-grid">
      {services.map((service) => <ServiceCard key={service.slug} service={service} />)}
    </div>
  ) : (
    <div className="category-grid">
      {categoryData.map((item) => <CategoryCard key={item[0].en} item={item} />)}
    </div>
  );
}

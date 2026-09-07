export type Service = {
  slug: string;
  title: string;
  titleUrdu: string;
  authority: string;
  category: string;
  description: string;
  descriptionUrdu: string;
  capabilities: string[];
  prompts: string[];
  officialUrl: string;
  officialDomain: string;
  officialScope: string;
};

export type DirectoryResource = {
  name: string;
  nameUrdu: string;
  description: string;
  descriptionUrdu: string;
  url: string;
  domain: string;
};

export const services: Service[] = [
  {
    slug: 'passport', title: 'Passport assistance', titleUrdu: 'پاسپورٹ رہنمائی',
    authority: 'Directorate General of Immigration & Passports', category: 'Passport',
    description: 'Understand requirements and fees, find an office, and walk through a demo appointment journey.',
    descriptionUrdu: 'ضروری دستاویزات اور فیس سمجھیں، دفتر تلاش کریں، اور ڈیمو اپائنٹمنٹ کا سفر دیکھیں۔',
    capabilities: ['Grounded document checklists', 'Fee guidance from trusted content', 'Service-centre lookup', 'Demo appointment flow'],
    prompts: ['What documents do I need for a passport?', 'How much does a passport cost?', 'Find a passport office in Karachi'],
    officialUrl: 'https://dgip.gov.pk/', officialDomain: 'dgip.gov.pk', officialScope: 'Passport requirements and procedures',
  },
  {
    slug: 'driving-licence', title: 'Driving licence assistance', titleUrdu: 'ڈرائیونگ لائسنس رہنمائی',
    authority: 'Provincial traffic police and licensing authorities', category: 'Driving licence',
    description: 'Explore requirements and available office information for supported driving-licence questions.',
    descriptionUrdu: 'ڈرائیونگ لائسنس کے سوالات کے لیے ضروریات اور دستیاب دفتری معلومات دیکھیں۔',
    capabilities: ['Grounded document checklists', 'Available fee guidance', 'Service-centre lookup', 'Demo appointment flow'],
    prompts: ['What should I take for a driving licence?', 'Find a driving licence office in Lahore', 'Show my driving licence journey progress'],
    officialUrl: 'https://dlims.punjab.gov.pk/', officialDomain: 'dlims.punjab.gov.pk', officialScope: 'Driving licence information and services',
  },
];

export const directoryResources: DirectoryResource[] = [
  { name: 'NADRA', nameUrdu: 'نادرا', description: 'Identity documents and Pak Identity services.', descriptionUrdu: 'شناختی دستاویزات اور پاک آئیڈینٹیٹی خدمات۔', url: 'https://www.nadra.gov.pk/', domain: 'nadra.gov.pk' },
  { name: 'Federal Board of Revenue', nameUrdu: 'وفاقی بورڈ آف ریونیو', description: 'Official tax information and the Iris portal.', descriptionUrdu: 'سرکاری ٹیکس معلومات اور آئرس پورٹل۔', url: 'https://www.fbr.gov.pk/', domain: 'fbr.gov.pk' },
  { name: 'Pakistan Citizen Portal', nameUrdu: 'پاکستان سٹیزن پورٹل', description: 'Official channel for citizen feedback and complaints.', descriptionUrdu: 'شہری آراء اور شکایات کے لیے سرکاری ذریعہ۔', url: 'https://citizenportal.gov.pk/', domain: 'citizenportal.gov.pk' },
];

export const getService = (slug: string) => services.find((service) => service.slug === slug);

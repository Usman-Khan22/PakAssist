import { services, getService, type Service } from '../data';

export type DashboardData = {
  user: string;
  stats: { value: string; label: string; detail: string }[];
};

export function getServices(): Service[] {
  return services;
}

export function getServiceBySlug(slug: string): Service | undefined {
  return getService(slug);
}

export function sendChatMessage(text: string): { text: string; source: string } {
  return {
    text: `Here is a practical guide based on the information available for: ${text}`,
    source: 'PakAssist mock guidance',
  };
}

export function getDashboardData(): DashboardData {
  return {
    user: 'Ahmed',
    stats: [
      { value: '3', label: 'Active Applications', detail: 'Across 2 services' },
      { value: '5 / 8', label: 'Documents Prepared', detail: 'Passport Renewal' },
      { value: '1', label: 'Upcoming Appointment', detail: 'Islamabad · 18 Jun' },
    ],
  };
}

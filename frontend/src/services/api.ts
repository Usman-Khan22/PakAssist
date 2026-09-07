import { services, getService } from '../data';
import { copy, type LocalizedText } from '../translations';

// Preserve the existing English mock API response shape; the UI consumes bilingual data directly.
type English<T> = T extends LocalizedText ? string : T extends Array<infer U> ? English<U>[] : T extends object ? { [K in keyof T]: English<T[K]> } : T;
function english<T>(value: T): English<T> {
  if (Array.isArray(value)) return value.map(english) as English<T>;
  if (value && typeof value === 'object') {
    if ('en' in value && 'ur' in value) return value.en as English<T>;
    return Object.fromEntries(Object.entries(value).map(([key, entry]) => [key, english(entry)])) as English<T>;
  }
  return value as English<T>;
}
type Service = English<(typeof services)[number]>;

export type DashboardData = {
  user: string;
  stats: { value: string; label: string; detail: string }[];
};

export function getServices(): Service[] {
  return english(services);
}

export function getServiceBySlug(slug: string): Service | undefined {
  const service = getService(slug);
  return service ? english(service) : undefined;
}

export function sendChatMessage(text: string): { text: string; source: string } {
  return {
    text: copy.apiChatReply.en.replace('{query}', text),
    source: copy.mockGuidance.en,
  };
}

export function getDashboardData(): DashboardData {
  return {
    user: copy.demoUser.en,
    stats: [
      { value: '3', label: copy.activeApplications.en, detail: copy.across2Services.en },
      { value: '5 / 8', label: copy.documentsPrepared.en, detail: copy.passportRenewal.en },
      { value: '1', label: copy.upcomingAppointment.en, detail: copy.islamabad18Jun.en },
    ],
  };
}

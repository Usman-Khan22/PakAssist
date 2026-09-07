import { getService, services, type Service } from '../data';
import type { Language } from '../language';

export type Session = { id: string; createdAt: string };
export type Source = { id: string; title: string; kind: 'official' | 'upload'; url?: string; detail?: string };
export type Upload = { id: string; file: File; name: string; size: number; mediaType: string; previewUrl?: string };
export type JourneyProgress = { service: string; steps: { label: string; status: 'pending' | 'reviewed' }[] };
export type Appointment = { office: string; date: string; time: string; status: 'demo' };
export type ServiceCenter = { name: string; city?: string; region?: string; address?: string };
export type ChatResponse = { response: string; sources: Source[]; journey?: JourneyProgress; appointment?: Appointment; serviceCenters?: ServiceCenter[]; suggestions?: string[] };
export type SendChatRequest = { sessionId: string; message: string; language: Language; upload?: Upload };

export function getServices(): Service[] { return services; }
export function getServiceBySlug(slug: string): Service | undefined { return getService(slug); }
export async function createSession(): Promise<Session> { return { id: crypto.randomUUID(), createdAt: new Date().toISOString() }; }
const wait = (milliseconds: number) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));

export async function sendChatMessage(request: SendChatRequest): Promise<ChatResponse> {
  await wait(550);
  const text = request.message.toLowerCase();
  if (text.includes('[demo error]')) throw new Error('The local response preview could not be loaded.');
  if (request.upload) return { response: request.language === 'ur' ? 'فائل اس مقامی انٹرفیس میں منسلک ہے۔ دستاویز کا اصل تجزیہ بیک اینڈ منسلک ہونے کے بعد ہوگا۔' : 'Your file is attached in this local interface preview. Actual document analysis will run after the backend is connected.', sources: [{ id: request.upload.id, title: request.upload.name, kind: 'upload', detail: 'Local attachment preview — not processed' }], suggestions: ['What documents do I need for a passport?', 'How much does it cost?'] };
  const isDriving = text.includes('driv') || text.includes('licen') || text.includes('لائسنس');
  const isPassport = text.includes('passport') || text.includes('پاسپورٹ');
  if (!isDriving && !isPassport) return {
    response: request.language === 'ur' ? 'یہ فرنٹ اینڈ ابھی مقامی ڈیمو ہے۔ پاسپورٹ یا ڈرائیونگ لائسنس کا نام لے کر سوال پوچھیں؛ مکمل جواب بیک اینڈ منسلک ہونے کے بعد دستیاب ہوگا۔' : 'This frontend is currently a local demo. Ask a question that names passport or driving licence; full guidance will be available after backend connection.',
    sources: [], suggestions: ['What documents do I need for a passport?', 'What should I take for a driving licence?'],
  };
  const service = isDriving ? services[1] : services[0];
  const source: Source = { id: service.slug, title: service.authority, kind: 'official', url: service.officialUrl, detail: service.officialDomain };
  if (text.includes('progress') || text.includes('journey')) return { response: request.language === 'ur' ? 'یہ مقامی سفر کے جزو کا پیش نظارہ ہے۔ کوئی سرکاری درخواست یا حیثیت نہیں بنائی گئی۔' : 'This is a local journey-component preview. No government application or status has been created.', sources: [], journey: { service: request.language === 'ur' ? service.titleUrdu : service.title, steps: ['Requirements', 'Fees', 'Service centre', 'Demo appointment'].map((label) => ({ label, status: 'pending' })) } };
  if (text.includes('appointment') || text.includes('slot') || text.includes('book')) return { response: request.language === 'ur' ? 'نیچے موجود اپائنٹمنٹ کارڈ صرف انٹرفیس ڈیمو ہے۔ یہ حقیقی وقت یا سرکاری بکنگ نہیں۔' : 'The appointment card below is a UI demonstration only. It is not a live slot or government booking.', sources: [source], appointment: { office: 'Selected service centre', date: 'Choose after backend connection', time: 'No live time selected', status: 'demo' } };
  return { response: request.language === 'ur' ? `${service.titleUrdu} کے لیے یہ مقامی ڈیمو قابلِ اعتماد ذرائع دکھانے کے لیے تیار ہے۔ مکمل سرکاری رہنمائی بیک اینڈ منسلک ہونے کے بعد یہاں ظاہر ہوگی۔` : `This local demo is ready to show grounded ${service.category.toLowerCase()} guidance and its sources. The full trusted answer will appear here after backend connection.`, sources: [source], suggestions: service.prompts.slice(0, 2) };
}

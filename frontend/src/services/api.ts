import { getService, services, type Service } from '../data';
import type { Language } from '../language';
import { apiRequest, jsonPost } from './client';

export type Session = { id: string; createdAt: string };
export type Source = { id: string; title: string; kind: 'official' | 'upload'; url?: string; detail?: string };
export type Upload = { id: string; file: File; name: string; size: number; mediaType: string; previewUrl?: string };
export type ChatResponse = { response: string; sources: Source[]; suggestions?: string[] };
export type SendChatRequest = { sessionId: string; message: string; language: Language; upload?: Upload };

export function getServices(): Service[] { return services; }
export function getServiceBySlug(slug: string): Service | undefined { return getService(slug); }
let currentSession: Session | null = null;
let pendingSession: Promise<Session> | null = null;
export function resetSession() { currentSession = null; sessionStorage.removeItem('pakassist-session'); }
export async function createSession(): Promise<Session> {
  if (currentSession) return currentSession;
  const saved = sessionStorage.getItem('pakassist-session');
  if (saved) { currentSession = { id: saved, createdAt: '' }; return currentSession; }
  if (!pendingSession) pendingSession = apiRequest('/sessions', jsonPost()).then(r => r.json()).then(data => {
    currentSession = { id: data.session_id, createdAt: new Date().toISOString() };
    sessionStorage.setItem('pakassist-session', currentSession.id);
    return currentSession;
  }).finally(() => { pendingSession = null; });
  return pendingSession;
}
export async function checkHealth(): Promise<void> { await apiRequest('/health'); }
export async function sendChatMessage(request: SendChatRequest): Promise<ChatResponse> {
  let response: Response;
  if (request.upload) {
    const body = new FormData(); body.append('file', request.upload.file); body.append('message', request.message);
    response = await apiRequest(`/sessions/${encodeURIComponent(request.sessionId)}/upload`, { method: 'POST', body });
  } else response = await apiRequest('/chat', jsonPost({ session_id: request.sessionId, message: request.message }));
  const data = await response.json();
  return { response: data.response, sources: data.sources.map((source: { label: string; origin: string; section?: string; confidence?: string; source_url?: string }, index: number) => ({
    id: String(index), title: source.label, kind: source.origin === 'user_upload' ? 'upload' : 'official',
    url: source.source_url && /^https?:\/\//i.test(source.source_url) ? source.source_url : undefined,
    detail: [source.section, source.confidence].filter(Boolean).join(' · '),
  })) };
}
export async function synthesizeSpeech(text: string): Promise<Blob> { return (await apiRequest('/voice/tts', jsonPost({ text }))).blob(); }

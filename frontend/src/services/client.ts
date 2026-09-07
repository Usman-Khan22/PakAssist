const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001').replace(/\/$/, '');
export async function apiRequest(path: string, init?: RequestInit): Promise<Response> {
  let response: Response;
  try { response = await fetch(`${baseUrl}${path}`, init); }
  catch { throw new Error('Cannot reach PakAssist. Check that the backend is running on port 8001.'); }
  if (!response.ok) {
    if (import.meta.env.DEV) console.error('PakAssist API', path, response.status);
    throw new Error(response.status === 404 ? 'This session has expired. Clear chat to start a new conversation.' : response.status === 502 ? 'The AI provider is temporarily unavailable. Please try again.' : response.status === 503 ? 'This service is not configured on the backend.' : response.status >= 500 ? 'PakAssist could not process this request. Please try again.' : 'The request was rejected. Check your message and attachment, then try again.');
  }
  return response;
}
export const jsonPost = (body?: unknown): RequestInit => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });

import { useSyncExternalStore } from 'react';
import { copy, type Language, type LocalizedText, type TranslationKey } from './translations';

const storageKey = 'pakassist-language';
const listeners = new Set<() => void>();
function readLanguage(): Language {
  try { return localStorage.getItem(storageKey) === 'ur' ? 'ur' : 'en'; }
  catch { return 'en'; }
}
let language: Language = readLanguage();
const byEnglish = new Map<string, LocalizedText>(Object.values(copy).map(value => [value.en, value]));

/** Unicode isolates keep official acronyms, domains and identifiers readable in Urdu prose. */
export function isolateLatin(text: string, selected: Language): string {
  const clean = text.replace(/[\u2066-\u2069]/g, '');
  return selected === 'ur' ? clean.replace(/[A-Za-z0-9][A-Za-z0-9@._:/&+’'–, -]*[A-Za-z0-9]|[A-Za-z0-9]/g, '\u2066$&\u2069') : clean;
}
export function localizeText(value: string | LocalizedText, selected: Language): string {
  return isolateLatin(typeof value === 'string' ? value : value[selected], selected);
}
/** Recognize authored search suggestions arriving through a URL; retain arbitrary user queries. */
export function authoredText(value: string): string | LocalizedText { return byEnglish.get(value) ?? value; }
export function applyLanguage(urdu: boolean) {
  language = urdu ? 'ur' : 'en';
  document.documentElement.lang = language;
  document.documentElement.dir = urdu ? 'rtl' : 'ltr';
  document.body.classList.toggle('urdu-mode', urdu);
  document.title = copy.pakassistGovernmentServicesMadeSimple[language];
  listeners.forEach(callback => callback());
}
export function getStoredLanguage() { return language === 'ur'; }
export function setStoredLanguage(urdu: boolean) {
  try { localStorage.setItem(storageKey, urdu ? 'ur' : 'en'); } catch { /* Switch even if storage is unavailable. */ }
  applyLanguage(urdu);
}
function subscribe(callback: () => void) {
  listeners.add(callback);
  return () => { listeners.delete(callback); };
}
window.addEventListener('storage', event => {
  if (event.key === storageKey || event.key === null) applyLanguage(readLanguage() === 'ur');
});
const tables = Object.fromEntries((['en', 'ur'] as const).map(selected => [selected,
  Object.fromEntries(Object.entries(copy).map(([key, value]) => [key, isolateLatin(value[selected], selected)])),
])) as Record<Language, Record<TranslationKey, string>>;
export function useLanguage() {
  const selected = useSyncExternalStore(subscribe, () => language, () => 'en' as Language);
  return { language: selected, t: tables[selected], localize: (value: string | LocalizedText) => localizeText(value, selected) };
}
export function useUrdu() { return useLanguage().language === 'ur'; }

import { useVoice } from './services/useVoice';
import { createContext, useContext, useEffect, useId, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { Link, NavLink, Route, Routes, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowRight, Building2, Check, CheckCheck, ChevronRight, CircleHelp, Copy, ExternalLink, FileText, Globe2, Menu, MessageCircle, Mic, Paperclip, Search, Send, ShieldCheck, Square, Trash2, Volume2, X } from 'lucide-react';
import { directoryResources, type Service } from './data';
import { applyLanguage, getInitialLanguage, translate, type Language } from './language';
import { resetSession, createSession, getServiceBySlug, getServices, sendChatMessage, type ChatResponse, type Source, type Upload } from './services/api';

const supportedServices = getServices();

type LanguageValue = { language: Language; setLanguage: (value: Language) => void; t: (text: string) => string };
const LanguageContext = createContext<LanguageValue | null>(null);
function useLanguage() { const value = useContext(LanguageContext); if (!value) throw new Error('Language provider missing'); return value; }

export type VoiceState = 'idle' | 'listening' | 'processing' | 'disabled' | 'error';
export type ReaderTarget = { type: 'page' } | { type: 'message'; id: string };
export type ReadAloudState = { status: 'idle' | 'speaking' | 'paused' | 'error'; target?: ReaderTarget };
export type VoiceUiIntegration = {
  voiceState: VoiceState;
  readAloudState: ReadAloudState;
  onVoiceClick?: () => void;
  onReadPage?: (root: HTMLElement) => void;
  onReadMessage?: (messageId: string, text: string) => void;
  onStopReading?: () => void;
};

type AppProps = { voiceUi?: VoiceUiIntegration };
const disconnectedVoiceUi: VoiceUiIntegration = { voiceState: 'disabled', readAloudState: { status: 'idle' } };
const VoiceUiContext = createContext<VoiceUiIntegration>(disconnectedVoiceUi);
function useVoiceUi() { return useContext(VoiceUiContext); }

function sameReader(left?: ReaderTarget, right?: ReaderTarget) {
  return left?.type === right?.type && (left?.type !== 'message' || (right?.type === 'message' && left.id === right.id));
}

function ReadAloudButton({ target, text, compact = false }: { target: ReaderTarget; text?: string; compact?: boolean }) {
  const { t } = useLanguage();
  const voiceUi = useVoiceUi();
  const active = voiceUi.readAloudState.status === 'speaking' && sameReader(voiceUi.readAloudState.target, target);
  const handler = target.type === 'page' ? voiceUi.onReadPage : voiceUi.onReadMessage;
  const label = active ? t('Stop reading') : t(target.type === 'page' ? 'Read page' : 'Read response');
  const anotherReaderActive = voiceUi.readAloudState.status === 'speaking' && !active;
  const disabled = !handler || ((active || anotherReaderActive) && !voiceUi.onStopReading);
  const activate = () => {
    if (active) voiceUi.onStopReading?.();
    else {
      if (anotherReaderActive) voiceUi.onStopReading?.();
      if (target.type === 'page') {
        const root = document.getElementById('main-content');
        if (root) voiceUi.onReadPage?.(root);
      } else voiceUi.onReadMessage?.(target.id, text ?? '');
    }
  };
  return <button type="button" className={`read-button ${compact ? 'compact' : ''} ${active ? 'active' : ''}`} onClick={activate} disabled={disabled} aria-label={label} aria-controls={target.type === 'page' ? 'main-content' : `message-${target.id}`} aria-pressed={active} title={label}>{active ? <Square size={compact ? 16 : 17} /> : <Volume2 size={compact ? 17 : 18} />}<span>{label}</span></button>;
}

function VoiceButton() {
  const { t } = useLanguage();
  const { voiceState, onVoiceClick } = useVoiceUi();
  const labels: Record<VoiceState, string> = { idle: 'Ask with voice', listening: 'Stop voice input', processing: 'Voice input processing', disabled: 'Ask with voice', error: 'Ask with voice' };
  const label = t(labels[voiceState]);
  return <button type="button" className={`icon-button voice-button ${voiceState}`} onClick={onVoiceClick} disabled={!onVoiceClick || voiceState === 'disabled' || voiceState === 'processing'} aria-label={label} aria-describedby={voiceState !== 'idle' && voiceState !== 'disabled' ? 'voice-input-status' : undefined} aria-pressed={voiceState === 'listening'} title={label}><Mic size={20} /></button>;
}

function Logo() {
  return <Link className="brand" to="/" aria-label="PakAssist home"><span className="brand-mark" aria-hidden="true">P</span><span><b>PakAssist</b><small>Citizen guidance</small></span></Link>;
}

function Header() {
  const { language, setLanguage, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const location = useLocation();
  useEffect(() => setOpen(false), [location.pathname]);
  const links = [{ to: '/services', label: 'Services' }, { to: '/how-it-works', label: 'How it works' }, { to: '/#official-sources', label: 'Official sources' }, { to: '/about', label: 'About' }];
  return <header className="site-header"><div className="shell nav-shell">
    <Logo />
    <button className="icon-button menu-button" aria-label={t(open ? 'Close navigation' : 'Open navigation')} aria-expanded={open} onClick={() => setOpen(!open)}><Menu size={22} /></button>
    <nav className={open ? 'main-nav is-open' : 'main-nav'} aria-label={t('Main navigation')}>
      {links.map((link) => <NavLink key={link.to} to={link.to} className={({ isActive }) => isActive && !link.to.includes('#') ? 'active' : ''}>{t(link.label)}</NavLink>)}
      <div className="accessibility-controls" aria-label={t('Accessibility controls')}><ReadAloudButton target={{ type: 'page' }} /></div>
      <div className="language-switch" aria-label={t('Choose language')}>
        <button className={language === 'en' ? 'selected' : ''} onClick={() => setLanguage('en')} lang="en">EN</button>
        <span aria-hidden="true">/</span>
        <button className={language === 'ur' ? 'selected' : ''} onClick={() => setLanguage('ur')} lang="ur">اردو</button>
      </div>
      <Link className="button button-primary nav-cta" to="/chat"><MessageCircle size={18} />{t('Ask PakAssist')}</Link>
    </nav>
  </div></header>;
}

function Footer() {
  const { t } = useLanguage();
  return <footer className="site-footer"><div className="shell footer-grid">
    <div><Logo /><p>{t('Clear guidance for selected Pakistani public services.')}</p></div>
    <nav aria-label={t('Footer navigation')}><Link to="/services">{t('Services')}</Link><Link to="/how-it-works">{t('How it works')}</Link><Link to="/about">{t('About')}</Link></nav>
    <p className="footer-note">{t('Prototype only. PakAssist is not a government authority and does not submit applications or make real bookings.')}</p>
  </div></footer>;
}

function PageLayout({ children }: { children: React.ReactNode }) { const { t } = useLanguage(); return <><a className="skip-link" href="#main-content">{t('Skip to main content')}</a><Header /><main id="main-content" data-read-aloud-root tabIndex={-1}>{children}</main><Footer /></>; }

function SearchBox({ large = false }: { large?: boolean }) {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [active, setActive] = useState(-1);
  const prompts = supportedServices.flatMap((service) => service.prompts);
  const matches = query.trim() ? prompts.filter((item) => item.toLowerCase().includes(query.toLowerCase())).slice(0, 5) : [];
  const submit = (value = query) => { if (value.trim()) navigate(`/chat?q=${encodeURIComponent(value.trim())}`); };
  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (!matches.length) return;
    if (event.key === 'ArrowDown') { event.preventDefault(); setActive((current) => Math.min(current + 1, matches.length - 1)); }
    if (event.key === 'ArrowUp') { event.preventDefault(); setActive((current) => Math.max(current - 1, 0)); }
    if (event.key === 'Enter' && active >= 0) { event.preventDefault(); submit(matches[active]); }
    if (event.key === 'Escape') { setQuery(''); setActive(-1); }
  };
  return <div className={large ? 'search-wrap search-large' : 'search-wrap'}>
    <form className="search-box" onSubmit={(event) => { event.preventDefault(); submit(); }} role="search"><Search aria-hidden="true" size={22} /><label className="sr-only" htmlFor="service-search">{t('Search or ask a question')}</label><input id="service-search" value={query} onChange={(event) => { setQuery(event.target.value); setActive(-1); }} onKeyDown={onKeyDown} placeholder={t('Search or ask a question')} autoComplete="off" aria-controls="search-suggestions" aria-expanded={matches.length > 0} />{query && <button type="button" className="search-clear" onClick={() => setQuery('')} aria-label="Clear search"><X size={18} /></button>}<button className="button button-primary" type="submit">{t('Ask your question')}<ArrowRight size={18} /></button></form>
    {matches.length > 0 && <ul id="search-suggestions" className="search-suggestions" role="listbox">{matches.map((item, index) => <li key={item} role="option" aria-selected={index === active}><button onMouseDown={(event) => event.preventDefault()} onClick={() => submit(item)}>{t(item)}<ChevronRight size={16} /></button></li>)}</ul>}
  </div>;
}

function SectionHeading({ eyebrow, title, body, centered = false }: { eyebrow?: string; title: string; body?: string; centered?: boolean }) {
  const { t } = useLanguage();
  return <div className={centered ? 'section-heading centered' : 'section-heading'}>{eyebrow && <p className="eyebrow">{t(eyebrow)}</p>}<h2>{t(title)}</h2>{body && <p>{t(body)}</p>}</div>;
}

function ServiceCard({ service }: { service: Service }) {
  const { language, t } = useLanguage();
  return <article className="service-card"><div className="service-icon" aria-hidden="true">{service.slug === 'passport' ? <FileText /> : <Building2 />}</div><p className="kicker">{t(service.category)}</p><h3>{language === 'ur' ? service.titleUrdu : service.title}</h3><p>{language === 'ur' ? service.descriptionUrdu : service.description}</p><Link className="text-link" to={`/services/${service.slug}`}>{t('View service')}<ArrowRight size={17} /></Link></article>;
}

function OfficialSources() {
  const { t } = useLanguage();
  return <section className="section official-section" id="official-sources"><div className="shell"><SectionHeading eyebrow="Official sources" title="Explore official sources" body="Direct links to the authorities behind the information." />
    <div className="source-grid">{supportedServices.map((service) => <a className="official-card" href={service.officialUrl} target="_blank" rel="noreferrer" key={service.slug}><ShieldCheck aria-hidden="true" /><span><b className="ltr-text">{service.authority}</b><em>{t(service.officialScope)}</em><small className="ltr-text">{service.officialDomain}</small></span><ExternalLink size={17} aria-hidden="true" /></a>)}</div>
  </div></section>;
}

function Home() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const suggestions = ['What documents do I need for a passport?', 'How much does a passport cost?', 'Find a driving licence office in Lahore'];
  return <PageLayout>
    <section className="hero"><div className="shell hero-inner"><p className="eyebrow"><ShieldCheck size={17} />{t('A clearer path through public services')}</p><h1>{t('Government services, explained clearly.')}</h1><p className="hero-lead">{t('Ask about passport or driving licence requirements, fees, offices, and your next step.')}</p><SearchBox large /><div className="prompt-row" aria-label="Suggested questions">{suggestions.map((item) => <button key={item} onClick={() => navigate(`/chat?q=${encodeURIComponent(item)}`)}>{t(item)}</button>)}</div></div></section>
    <section className="trust-strip" aria-label="PakAssist principles"><div className="shell trust-grid"><div><ShieldCheck /><span><b>{t('Trusted guidance')}</b><small>{t('Grounded in curated government information')}</small></span></div><div><Globe2 /><span><b>{t('English and Urdu')}</b><small>{t('Switch language at any time')}</small></span></div><div><FileText /><span><b>{t('Your privacy')}</b><small>{t('Uploads stay within the current session')}</small></span></div></div></section>
    <section className="section"><div className="shell"><SectionHeading eyebrow="Supported assistance" title="Supported services" body="Focused help for two common citizen journeys." /><div className="service-grid">{supportedServices.map((service) => <ServiceCard service={service} key={service.slug} />)}</div></div></section>
    <section className="section steps-section"><div className="shell"><SectionHeading title="How it works" body="Three simple steps from question to next action." centered /><div className="steps-grid">{[[CircleHelp,'Start with a question','PakAssist identifies the service and what you need.'],[ShieldCheck,'Check trusted information','Answers use curated knowledge and show their sources.'],[Check,'Take the next step','Get a checklist, fee guidance, office options, or a demo appointment.']].map(([Icon,title,body], index) => { const StepIcon = Icon as typeof CircleHelp; return <article className="step-card" key={title as string}><span className="step-number">0{index + 1}</span><StepIcon aria-hidden="true" /><h3>{t(title as string)}</h3><p>{t(body as string)}</p></article>; })}</div></div></section>
    <section className="section"><div className="shell cta-panel"><div><h2>{t('Ready to find your next step?')}</h2><p>{t('Open the assistant and ask in your own words.')}</p></div><Link className="button button-light" to="/chat">{t('Ask PakAssist')}<ArrowRight size={18} /></Link></div></section>
    <OfficialSources />
  </PageLayout>;
}

function ServicesPage() {
  const { language, t } = useLanguage();
  const [query, setQuery] = useState('');
  const filtered = supportedServices.filter((service) => `${service.title} ${service.titleUrdu} ${service.category}`.toLowerCase().includes(query.toLowerCase()));
  return <PageLayout><section className="page-hero"><div className="shell narrow"><p className="eyebrow">{t('Supported assistance')}</p><h1>{t('Services')}</h1><p>{t('Focused guidance where PakAssist currently has a dedicated knowledge and action flow.')}</p><div className="inline-search"><Search size={20} /><label className="sr-only" htmlFor="services-filter">{t('Filter services')}</label><input id="services-filter" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t('Search or ask a question')} />{query && <button onClick={() => setQuery('')} aria-label="Clear filter"><X size={18} /></button>}</div></div></section>
    <section className="section compact-top"><div className="shell">{filtered.length ? <div className="service-grid">{filtered.map((service) => <ServiceCard service={service} key={service.slug} />)}</div> : <div className="empty-state"><Search /><h2>{t('No matching service')}</h2><p>{t('Try passport or driving licence, or ask PakAssist directly.')}</p><Link className="button button-primary" to="/chat">{t('Ask PakAssist')}</Link></div>}</div></section>
    <section className="section directory-section"><div className="shell"><SectionHeading title="Other government resources" body="These are official directory links, not PakAssist agent workflows." /><div className="directory-grid">{directoryResources.map((resource) => <a href={resource.url} target="_blank" rel="noreferrer" className="directory-card" key={resource.name}><span><b>{language === 'ur' ? resource.nameUrdu : resource.name}</b><small>{language === 'ur' ? resource.descriptionUrdu : resource.description}</small><em className="ltr-text">{resource.domain}</em></span><ExternalLink size={18} /></a>)}</div></div></section>
  </PageLayout>;
}

function ServiceDetail() {
  const { slug } = useParams(); const service = slug ? getServiceBySlug(slug) : undefined; const { language, t } = useLanguage();
  if (!service) return <PageLayout><section className="page-hero"><div className="shell narrow"><h1>{t('Service not found')}</h1><Link className="text-link" to="/services">{t('Back to services')}<ArrowRight size={17} /></Link></div></section></PageLayout>;
  return <PageLayout><section className="detail-hero"><div className="shell detail-grid"><div><Link className="back-link" to="/services">← {t('Back to services')}</Link><p className="eyebrow">{t(service.category)}</p><h1>{language === 'ur' ? service.titleUrdu : service.title}</h1><p className="hero-lead">{language === 'ur' ? service.descriptionUrdu : service.description}</p><Link className="button button-primary" to={`/chat?q=${encodeURIComponent(service.prompts[0])}`}>{t('Ask PakAssist')}<ArrowRight size={18} /></Link></div><aside className="authority-card"><ShieldCheck /><p>{t('Source authority')}</p><h2>{service.authority}</h2><a href={service.officialUrl} target="_blank" rel="noreferrer">{t('Official website')}<ExternalLink size={17} /></a></aside></div></section>
    <section className="section"><div className="shell detail-content"><div><SectionHeading title="What PakAssist can help with" /><ul className="check-list">{service.capabilities.map((item) => <li key={item}><Check size={18} />{t(item)}</li>)}</ul></div><div><SectionHeading title="Example questions" /><div className="question-list">{service.prompts.map((prompt) => <Link to={`/chat?q=${encodeURIComponent(prompt)}`} key={prompt}>{t(prompt)}<ArrowRight size={17} /></Link>)}</div></div></div><div className="shell"><p className="notice"><ShieldCheck size={18} />{t('This prototype does not submit government applications or make real bookings. Always confirm time-sensitive details on the official website.')}</p></div></section>
  </PageLayout>;
}

type ChatMessage = { id: string; role: 'user' | 'assistant'; text: string; result?: ChatResponse; error?: boolean };
let conversation: ChatMessage[] = [];

function SourceList({ sources }: { sources: Source[] }) {
  const { t } = useLanguage();
  if (!sources.length) return <p className="no-sources"><CircleHelp size={16} />{t('No sources were returned for this response.')}</p>;
  return <div className="response-sources" aria-label="Response sources">{sources.map((source) => { const content = <><span className={`source-kind ${source.kind}`}><ShieldCheck size={14} />{t(source.kind === 'official' ? 'Official source' : 'Uploaded document')}</span><b>{source.title}</b>{source.detail && <small className="ltr-text">{source.detail}</small>}</>; return source.url ? <a href={source.url} target="_blank" rel="noreferrer" key={source.id}>{content}<ExternalLink size={16} /></a> : <div className="source-item" key={source.id}>{content}</div>; })}</div>;
}

function MessageActions({ messageId, text }: { messageId: string; text: string }) {
  const { t } = useLanguage();
  const [copied, setCopied] = useState(false);
  const copyResponse = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };
  return <div className="message-actions" aria-label={t('Response actions')}>
    <ReadAloudButton target={{ type: 'message', id: messageId }} text={text} compact />
    <button type="button" className="message-action-button" onClick={copyResponse} aria-label={t(copied ? 'Response copied' : 'Copy response')} title={t(copied ? 'Response copied' : 'Copy response')}>{copied ? <CheckCheck size={16} /> : <Copy size={16} />}<span>{t(copied ? 'Copied' : 'Copy')}</span></button>
  </div>;
}

function ChatPage() {
  const { language, t } = useLanguage(); const [params] = useSearchParams();
  const [messages, updateMessages] = useState<ChatMessage[]>(conversation);
  const setMessages = (value: ChatMessage[] | ((current: ChatMessage[]) => ChatMessage[])) => { conversation = typeof value === 'function' ? value(conversation) : value; updateMessages(conversation); }; const [input, setInput] = useState(params.get('q') ?? ''); const [upload, setUpload] = useState<Upload | undefined>(); const [loading, setLoading] = useState(false); const [fileError, setFileError] = useState(''); const [lastRequest, setLastRequest] = useState<{ text: string; upload?: Upload }>();
  const fileRef = useRef<HTMLInputElement>(null); const endRef = useRef<HTMLDivElement>(null); const inputId = useId();
  const sending = useRef(false);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);
  useEffect(() => () => { if (upload?.previewUrl) URL.revokeObjectURL(upload.previewUrl); }, [upload]);
  const chooseFile = (file?: File) => { setFileError(''); if (!file) return; if (!/\.(jpg|jpeg|png|webp|pdf)$/i.test(file.name)) { setFileError('Choose a JPG, PNG, WEBP, or PDF file.'); return; } if (upload?.previewUrl) URL.revokeObjectURL(upload.previewUrl); setUpload({ id: crypto.randomUUID(), file, name: file.name, size: file.size, mediaType: file.type, previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined }); };
  const runSend = async (text: string, selectedUpload?: Upload, spoken = false) => {
    if ((!text.trim() && !selectedUpload) || sending.current) return;
    sending.current = true; if (!spoken) voice.stop();
    const clean = text.trim() || 'Please inspect this uploaded document.';
    setMessages(current => [...current, { id: crypto.randomUUID(), role: 'user', text: selectedUpload ? clean + '\n' + selectedUpload.name : clean }]);
    setInput(''); setUpload(undefined); setLoading(true); setLastRequest({ text: clean, upload: selectedUpload });
    try {
      const session = await createSession();
      const result = await sendChatMessage({ sessionId: session.id, message: clean, language, upload: selectedUpload });
      setMessages(current => [...current, { id: crypto.randomUUID(), role: 'assistant', text: result.response, result }]);
      if (spoken) void voice.speak(result.response);
    } catch (error) {
      voice.stop();
      setMessages(current => [...current, { id: crypto.randomUUID(), role: 'assistant', text: error instanceof Error ? error.message : t('PakAssist is temporarily unavailable. Please try again.'), error: true }]);
    } finally { sending.current = false; setLoading(false); }
  };
  const [readerTarget, setReaderTarget] = useState<ReaderTarget>();
  const voice = useVoice(text => { setInput(text); void runSend(text, upload, true); }, loading);
  const voiceUi: VoiceUiIntegration = {
    voiceState: loading ? 'processing' : voice.status === 'unsupported' ? 'disabled' : voice.status === 'listening' ? 'listening' : voice.status === 'error' ? 'error' : 'idle',
    readAloudState: { status: voice.status === 'speaking' ? 'speaking' : 'idle', target: readerTarget },
    onVoiceClick: voice.listen, onReadMessage: (id, text) => { setReaderTarget({ type: 'message', id }); void voice.speak(text); }, onReadPage: root => { setReaderTarget({ type: 'page' }); void voice.speak(root.innerText); }, onStopReading: voice.stop,
  };
  const clearChat = () => { if (sending.current) return; voice.stop(); setMessages([]); conversation = []; setInput(''); setUpload(undefined); setFileError(''); setLastRequest(undefined); resetSession(); };
  return <VoiceUiContext.Provider value={voiceUi}><PageLayout><section className="chat-page"><div className="shell chat-shell"><div className="chat-heading"><div><p className="eyebrow">{t('Private session')}</p><h1>{t('PakAssist conversation')}</h1><p>{t('Session-based guidance')}</p></div><button className="button button-quiet" onClick={clearChat} disabled={loading || (!messages.length && !input)}><Trash2 size={18} />{t('Clear chat')}</button></div>
    <div className="chat-panel"><div className="messages" aria-live="polite">{messages.length === 0 && !loading && <div className="chat-empty"><span className="empty-mark"><MessageCircle /></span><h2>{t('Welcome to PakAssist')}</h2><p>{t('Ask a question to begin. You can also attach one image or PDF for the current message.')}</p><div className="suggestion-grid">{supportedServices.flatMap((service) => service.prompts.slice(0, 2)).map((prompt) => <button onClick={() => setInput(prompt)} key={prompt}>{t(prompt)}<ArrowRight size={16} /></button>)}</div></div>}
      {messages.map((message) => <article className={`message ${message.role} ${message.error ? 'error' : ''}`} key={message.id}><span className="message-role">{message.role === 'user' ? t('You') : 'PakAssist'}</span><div className="message-bubble" id={`message-${message.id}`}><p dir="auto">{message.text}</p>{message.result && <><SourceList sources={message.result.sources} />{message.result.suggestions && <div className="followups">{message.result.suggestions.map((suggestion) => <button onClick={() => setInput(suggestion)} key={suggestion}>{t(suggestion)}</button>)}</div>}</>}{message.error && lastRequest && <button className="text-button" onClick={() => runSend(lastRequest.text, lastRequest.upload)}>{t('Try again')}</button>}</div>{message.role === 'assistant' && !message.error && <MessageActions messageId={message.id} text={message.text} />}</article>)}
      {loading && <div className="message assistant"><span className="message-role">PakAssist</span><div className="message-bubble loading-bubble"><span /><span /><span /><em>{t(lastRequest?.upload ? 'Processing document…' : 'PakAssist is preparing a response')}</em></div></div>}<div ref={endRef} /></div>
      <div className="composer-wrap">{upload && <div className="upload-preview">{upload.previewUrl ? <img src={upload.previewUrl} alt="Attachment preview" /> : <FileText /> }<span><b className="ltr-text">{upload.name}</b><small>{(upload.size / 1024 / 1024).toFixed(1)} MB</small></span><button onClick={() => setUpload(undefined)} aria-label={t('Remove attachment')}><X size={18} /></button></div>}{fileError && <p className="field-error" role="alert">{fileError}</p>}
        <form className="composer" onSubmit={(event: FormEvent) => { event.preventDefault(); runSend(input, upload); }}><label className="sr-only" htmlFor={inputId}>{t('Type your message')}</label><textarea id={inputId} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); runSend(input, upload); } }} placeholder={t('Type your message')} rows={2} /><input ref={fileRef} type="file" accept=".jpg,.jpeg,.png,.webp,.pdf" hidden onChange={(event) => { chooseFile(event.target.files?.[0]); event.currentTarget.value = ''; }} /><button type="button" className="icon-button" onClick={() => fileRef.current?.click()} aria-label={t('Attach a file')} title={t('Attach a file')}><Paperclip /></button><VoiceButton /><button className="send-button" type="submit" disabled={loading || (!input.trim() && !upload)} aria-label={t('Send message')} title={t('Send message')}><Send /></button></form><p id="voice-input-status" className="voice-feedback" role={voice.error ? 'alert' : 'status'}>{voice.error || (voice.status === 'unsupported' ? t('Voice input is unsupported in this browser. You can continue typing.') : voice.status === 'listening' ? t('Listening…') + ' ' + voice.transcript : voice.status === 'speaking' ? t('Speaking…') : loading ? t('PakAssist is preparing a response') : '')}</p>{voice.status === 'speaking' && <button type="button" className="text-button" onClick={voice.stop}>{t('Stop reading')}</button>}<p className="composer-note">JPG, PNG, WEBP or PDF · one file per message</p></div>
    </div></div></section></PageLayout></VoiceUiContext.Provider>;
}

function Dashboard() {
  const { t } = useLanguage();
  return <PageLayout><section className="page-hero"><div className="shell narrow"><p className="eyebrow">{t('Session overview')}</p><h1>{t('My PakAssist Journey')}</h1><p>{t('A private, session-based view of the guidance steps you review.')}</p></div></section><section className="section compact-top"><div className="shell dashboard-layout"><div className="empty-state journey-empty"><span className="empty-mark"><FileText /></span><h2>{t(conversation.length ? 'Continue your journey' : 'No active journey yet')}</h2><p>{t('Ask about your journey progress in the current conversation.')}</p><Link className="button button-primary" to="/chat?q=Show%20my%20journey%20progress">{t('Start a journey')}<ArrowRight size={18} /></Link></div><aside className="privacy-card"><ShieldCheck /><h2>{t('Your privacy')}</h2><p>{t('Journey information is designed for the current session. This frontend does not contain government application records.')}</p></aside></div></section></PageLayout>;
}

function HowItWorks() {
  const { t } = useLanguage();
  return <PageLayout><section className="page-hero"><div className="shell narrow"><p className="eyebrow">{t('Built for clear next steps')}</p><h1>{t('How PakAssist works')}</h1><p>{t('A focused assistant for navigating selected public services.')}</p></div></section><section className="section compact-top"><div className="shell prose-layout"><div><h2>{t('From a question to useful guidance')}</h2><div className="vertical-steps">{[['01','Ask naturally','Write in English or Urdu. You can name the service now or clarify it in the conversation.'],['02','Review grounded help','The connected backend can retrieve trusted information, format checklists, and retain the active service during a session.'],['03','Choose a next step','Continue to fees, office options, journey progress, or a clearly labelled demo appointment flow.']].map(([n,title,body]) => <article key={n}><span>{n}</span><div><h3>{t(title)}</h3><p>{t(body)}</p></div></article>)}</div></div><aside className="info-panel"><h2>{t('What it does not do')}</h2><ul><li>{t('Submit a government application')}</li><li>{t('Guarantee fees, availability, or processing time')}</li><li>{t('Create a real appointment')}</li><li>{t('Replace an official authority')}</li></ul><Link className="button button-primary" to="/chat">{t('Ask PakAssist')}</Link></aside></div></section></PageLayout>;
}

function About() {
  const { t } = useLanguage();
  return <PageLayout><section className="page-hero"><div className="shell narrow"><p className="eyebrow">{t('Citizen-first design')}</p><h1>{t('About PakAssist')}</h1><p>{t('PakAssist is a prototype citizen-assistance experience for selected Pakistani public services.')}</p></div></section><section className="section compact-top"><div className="shell about-grid"><article><Globe2 /><h2>{t('What this prototype includes')}</h2><p>{t('English and Urdu guidance, trusted-source visibility, session-based follow-ups, document-upload interfaces, service-centre lookup, journey progress, and demo appointment interactions for supported services.')}</p></article><article><CircleHelp /><h2>{t('Current limitations')}</h2><p>{t('Coverage is limited, driving-licence office data is incomplete, and details may change.')}</p></article><article><ShieldCheck /><h2>{t('Privacy and uploads')}</h2><p>{t('Uploaded files are intended for temporary session use. This interface does not provide long-term accounts or government record storage.')}</p></article><article><FileText /><h2>{t('Prototype disclaimer')}</h2><p>{t('PakAssist is not a government authority. It does not submit applications, calculate GPS distance, check live government systems, or make real bookings.')}</p></article></div></section></PageLayout>;
}

function NotFound() { return <PageLayout><section className="page-hero"><div className="shell narrow"><p className="eyebrow">404</p><h1>Page not found</h1><p>The page you requested is not available.</p><Link className="button button-primary" to="/">Return home</Link></div></section></PageLayout>; }

export default function App({ voiceUi = disconnectedVoiceUi }: AppProps) {
  const [language, setLanguage] = useState<Language>(getInitialLanguage);
  const location = useLocation();
  useEffect(() => applyLanguage(language), [language]);
  useEffect(() => {
    if (location.hash) window.requestAnimationFrame(() => document.querySelector(location.hash)?.scrollIntoView());
    else window.scrollTo({ top: 0 });
  }, [location.pathname, location.hash]);
  const value = { language, setLanguage, t: (text: string) => translate(language, text) };
  return <LanguageContext.Provider value={value}><VoiceUiContext.Provider value={voiceUi}><Routes><Route path="/" element={<Home />} /><Route path="/services" element={<ServicesPage />} /><Route path="/services/:slug" element={<ServiceDetail />} /><Route path="/chat" element={<ChatPage />} /><Route path="/dashboard" element={<Dashboard />} /><Route path="/how-it-works" element={<HowItWorks />} /><Route path="/about" element={<About />} /><Route path="*" element={<NotFound />} /></Routes></VoiceUiContext.Provider></LanguageContext.Provider>;
}

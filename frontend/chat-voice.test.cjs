const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { transformSync } = require('rolldown/utils');

const longAnswer = [
  'There are three driving licence service centres in Lahore. Choose a centre that offers your required service.',
  '**1. Liberty Service Centre**',
  'Address: 45 Main Boulevard, Gulberg, Lahore.',
  'Phone: 042-12345678',
  '**2. Model Town Service Centre**',
  'Address: 17 Link Road, Model Town, Lahore.',
  'Phone: 042-87654321',
  '**3. Cantt Service Centre**',
  'Address: 90 Cantonment Road, Lahore.',
  'Phone: 042-11112222',
  'Sources: https://example.gov.pk/centres',
  'Confidence: high. Confirm opening hours before visiting.',
].join('\n');

const deferred = () => {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
};
const settle = () => new Promise(resolve => setImmediate(resolve));
const json = value => new Response(JSON.stringify(value), { headers: { 'Content-Type': 'application/json' } });
const wav = () => new Response(new Uint8Array([82, 73, 70, 70]), { headers: { 'Content-Type': 'audio/wav' } });

// Render the real component functions with persistent hook state. Network,
// recognition and audio are browser boundaries; application modules are real.
function chatHarness(t, { ttsReply = wav, chatReply = () => json({ response: longAnswer, sources: [] }) } = {}) {
  const savedGlobals = new Map(['window', 'sessionStorage', 'fetch', 'Audio'].map(name => [name, global[name]]));
  const savedCreateUrl = URL.createObjectURL;
  const savedRevokeUrl = URL.revokeObjectURL;
  const storage = new Map();
  const calls = [];
  let recognition;
  let currentHooks;
  let hookIndex;
  let tree;
  const hookStates = new Map();
  const contextValues = new Map();
  const Fragment = Symbol('Fragment');
  const language = { language: 'en', t: value => value, setLanguage() {} };
  const nextHook = initial => {
    const index = hookIndex++;
    if (!(index in currentHooks)) currentHooks[index] = initial();
    return [currentHooks, index];
  };
  const react = {
    createContext(defaultValue) {
      const context = { defaultValue };
      context.Provider = { context };
      return context;
    },
    useContext: context => contextValues.has(context) ? contextValues.get(context) : context.defaultValue ?? language,
    useState(initial) {
      const [state, index] = nextHook(() => typeof initial === 'function' ? initial() : initial);
      return [state[index], value => { state[index] = typeof value === 'function' ? value(state[index]) : value; }];
    },
    useRef(initial) { const [state, index] = nextHook(() => ({ current: initial })); return state[index]; },
    useId() { const [, index] = nextHook(() => null); return `test-input-${index}`; },
    useEffect() {},
  };
  const jsx = (type, props, key) => ({ type, props: props ?? {}, key });
  const moduleCache = new Map();
  const mocks = {
    react,
    'react/jsx-runtime': { jsx, jsxs: jsx, Fragment },
    'react-router-dom': {
      Link: 'a', NavLink: 'a', Route: 'route', Routes: 'routes',
      useLocation: () => ({ pathname: '/chat', hash: '' }), useNavigate: () => () => {},
      useParams: () => ({}), useSearchParams: () => [new URLSearchParams()],
    },
    'lucide-react': new Proxy({}, { get: (_, name) => `icon-${String(name)}` }),
    'react-markdown': { default: ({ children }) => jsx('div', { children }) },
    'remark-gfm': { default: () => {} },
  };
  const load = filename => {
    if (moduleCache.has(filename)) return moduleCache.get(filename);
    let source = fs.readFileSync(filename, 'utf8').replaceAll('import.meta.env', '({ DEV: false })');
    if (filename.endsWith('App.tsx')) source += '\nexport { ChatPage };';
    const transformed = transformSync(filename, source, { jsx: { runtime: 'automatic' }, target: 'es2022' });
    assert.deepEqual(transformed.errors, []);
    const names = [...transformed.code.matchAll(/export (?:async )?(?:function|const|let) (\w+)/g)].map(match => match[1]);
    let code = transformed.code
      .replace(/import \{([^}]+)\} from ["']([^"']+)["'];/g,
        (_, bindings, name) => `const {${bindings.replace(/\bas\b/g, ':')}} = require(${JSON.stringify(name)});`)
      .replace(/export \{([^}]+)\};/g, (_, bindings) => `Object.assign(exports, {${bindings}});`)
      .replace(/export default /g, '')
      .replace(/export /g, '');
    code += `\nObject.assign(exports, {${names.join(',')}});`;
    const module = { exports: {} };
    new Function('require', 'module', 'exports', code)(name => {
      if (name in mocks) return mocks[name];
      if (name === './data' || name === '../data') return { services: [], directoryResources: [], getService() {} };
      if (name === './language') return { getInitialLanguage: () => 'en', applyLanguage() {}, translate: (_, value) => value };
      if (name.startsWith('.')) {
        const base = path.resolve(path.dirname(filename), name);
        const resolved = ['.ts', '.tsx'].map(extension => `${base}${extension}`).find(fs.existsSync);
        if (resolved) return load(resolved);
      }
      throw new Error(`Unexpected application import: ${name}`);
    }, module, module.exports);
    moduleCache.set(filename, module.exports);
    return module.exports;
  };
  const renderNode = (node, location = 'root') => {
    if (node == null || typeof node === 'boolean') return null;
    if (Array.isArray(node)) return node.map((child, index) => renderNode(child, `${location}/${child?.key ?? index}`));
    if (typeof node !== 'object') return node;
    if (node.type === Fragment) return renderNode(node.props.children, `${location}/fragment`);
    if (node.type?.context) {
      const context = node.type.context;
      const previous = contextValues.get(context);
      contextValues.set(context, node.props.value);
      const child = renderNode(node.props.children, `${location}/provider`);
      if (previous === undefined) contextValues.delete(context); else contextValues.set(context, previous);
      return child;
    }
    if (typeof node.type === 'function') {
      const id = `${location}/${node.type.name}`;
      if (!hookStates.has(id)) hookStates.set(id, []);
      currentHooks = hookStates.get(id);
      hookIndex = 0;
      return renderNode(node.type(node.props), id);
    }
    return { ...node, children: renderNode(node.props.children, `${location}/${node.type}`) };
  };
  const all = (predicate, node = tree) => {
    if (Array.isArray(node)) return node.flatMap(child => all(predicate, child));
    if (!node || typeof node !== 'object') return [];
    return [...(predicate(node) ? [node] : []), ...all(predicate, node.children)];
  };
  const textContent = node => {
    if (Array.isArray(node)) return node.map(textContent).join('');
    if (typeof node === 'string' || typeof node === 'number') return String(node);
    if (!node || typeof node !== 'object') return '';
    return textContent(node.children);
  };
  const find = predicate => {
    const found = all(predicate);
    assert.equal(found.length, 1, 'Expected exactly one matching element');
    return found[0];
  };
  const isLoading = () => all(node => node.props.className === 'message-bubble loading-bubble').length > 0;
  global.window = { SpeechRecognition: class {
    constructor() { recognition = this; }
    start() {} stop() {} abort() {}
  } };
  global.sessionStorage = { getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key) };
  global.Audio = class { async play() {} pause() {} };
  URL.createObjectURL = () => 'blob:chat-voice-test';
  URL.revokeObjectURL = () => {};
  global.fetch = async (url, init) => {
    const request = { path: new URL(url).pathname, body: init?.body ? JSON.parse(init.body) : undefined };
    calls.push(request);
    if (request.path === '/sessions') return json({ session_id: 'shared-typed-and-voice-session' });
    if (request.path === '/chat') return chatReply(request);
    if (request.path === '/voice/tts') {
      render();
      request.loadingWhenTtsStarted = isLoading();
      return ttsReply(request);
    }
    throw new Error(`Unexpected request: ${request.path}`);
  };
  t.after(() => {
    for (const [name, value] of savedGlobals) {
      if (value === undefined) delete global[name]; else global[name] = value;
    }
    URL.createObjectURL = savedCreateUrl;
    URL.revokeObjectURL = savedRevokeUrl;
  });
  const { ChatPage } = load(path.join(__dirname, 'src', 'App.tsx'));
  function render() { tree = renderNode(jsx(ChatPage)); return tree; }
  render();
  return {
    calls, all, find, render, isLoading,
    type(text) {
      find(node => node.type === 'textarea').props.onChange({ target: { value: text } });
      render();
      find(node => node.type === 'form' && node.props.className === 'composer').props.onSubmit({ preventDefault() {} });
      render();
    },
    dictate(text) {
      find(node => node.type === 'button' && node.props['aria-label'] === 'Ask with voice').props.onClick();
      assert.equal(recognition.lang, 'en-PK');
      recognition.onresult({ results: [{ isFinal: true, 0: { transcript: text } }] });
      render();
    },
    assistantTexts: () => all(node => node.type === 'article' && node.props.className.includes('message assistant'))
      .flatMap(article => all(node => node.props.className === 'markdown-response', article).map(textContent)),
  };
}

test('typed chat displays the complete answer and speaks only after the existing Read response action', async t => {
  const chat = chatHarness(t);
  chat.type('Where can I renew my driving licence?');
  assert.equal(chat.isLoading(), true);
  await settle(); chat.render();
  assert.deepEqual(chat.assistantTexts(), [longAnswer]);
  assert.equal(chat.isLoading(), false);
  assert.equal(chat.calls.filter(call => call.path === '/voice/tts').length, 0);
  chat.find(node => node.type === 'button' && node.props['aria-label'] === 'Read response').props.onClick();
  await settle(); chat.render();
  assert.equal(chat.calls.filter(call => call.path === '/voice/tts').length, 1);
  assert.deepEqual(chat.assistantTexts(), [longAnswer]);
});

test('microphone chat clears loading and displays the full answer while concise TTS is pending, sharing the typed session', async t => {
  const pendingSpeech = deferred();
  const chat = chatHarness(t, { ttsReply: () => pendingSpeech.promise });
  chat.type('I live in Lahore.');
  await settle(); chat.render();
  chat.dictate('Driving licence centre kahan hai?');
  await settle(); chat.render();
  const speechCalls = chat.calls.filter(call => call.path === '/voice/tts');
  assert.equal(speechCalls.length, 1);
  assert.equal(speechCalls[0].loadingWhenTtsStarted, false);
  assert.equal(chat.isLoading(), false);
  assert.deepEqual(chat.assistantTexts(), [longAnswer, longAnswer]);
  assert.ok(speechCalls[0].body.text.length > 0 && speechCalls[0].body.text.length <= 500);
  assert.notEqual(speechCalls[0].body.text, longAnswer);
  assert.doesNotMatch(speechCalls[0].body.text, /Main Boulevard|042-|https:|Confidence:/i);
  assert.deepEqual(chat.calls.filter(call => call.path === '/chat').map(call => call.body.session_id),
    ['shared-typed-and-voice-session', 'shared-typed-and-voice-session']);
  assert.equal(chat.calls.filter(call => call.path === '/sessions').length, 1);
  pendingSpeech.resolve(wav());
  await settle();
});

test('microphone TTS failure preserves the successful answer without a chat error or retry', async t => {
  const chat = chatHarness(t, { ttsReply: () => new Response('', { status: 502 }) });
  chat.dictate('Show licence centres in Lahore.');
  await settle(); chat.render();
  assert.deepEqual(chat.assistantTexts(), [longAnswer]);
  assert.equal(chat.isLoading(), false);
  assert.equal(chat.all(node => node.type === 'article' && node.props.className.includes('error')).length, 0);
  assert.equal(chat.all(node => node.type === 'button' && node.props.children === 'Try again').length, 0);
  assert.match(chat.find(node => node.props.id === 'voice-input-status').props.children, /text answer is still available/);
});

test('retrying a failed microphone chat retains automatic speech and the same session', async t => {
  let attempts = 0;
  const chat = chatHarness(t, {
    chatReply: () => ++attempts === 1 ? new Response('', { status: 503 }) : json({ response: longAnswer, sources: [] }),
  });
  chat.dictate('Driving licence centre kahan hai?');
  await settle(); chat.render();
  assert.equal(chat.calls.filter(call => call.path === '/voice/tts').length, 0);
  await chat.find(node => node.type === 'button' && node.props.children === 'Try again').props.onClick();
  await settle(); chat.render();
  assert.equal(chat.assistantTexts().at(-1), longAnswer);
  assert.equal(chat.isLoading(), false);
  assert.equal(chat.calls.filter(call => call.path === '/voice/tts').length, 1);
  assert.deepEqual(chat.calls.filter(call => call.path === '/chat').map(call => call.body.session_id),
    ['shared-typed-and-voice-session', 'shared-typed-and-voice-session']);
});

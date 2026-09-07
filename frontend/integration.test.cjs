const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { stripTypeScriptTypes } = require('node:module');
function load(file, imports = {}) {
  const source = fs.readFileSync(`${__dirname}/src/${file}`, 'utf8').replaceAll('import.meta.env', '({ DEV: false })');
  let code = stripTypeScriptTypes(source);
  const names = [...code.matchAll(/export (?:async )?(?:function|const|let) (\w+)/g)].map(match => match[1]);
  code = code.replace(/import \{([^}]+)\} from '([^']+)';/g, 'const {$1} = require(\'$2\');').replace(/export /g, '');
  code += `\nObject.assign(exports, {${names.join(',')}});`;
  const module = { exports: {} };
  new Function('require', 'module', 'exports', code)(name => {
    if (name in imports) return imports[name];
    throw new Error(`Unexpected import ${name}`);
  }, module, module.exports);
  return module.exports;
}
test('real contracts: one session, exact multilingual answer, multipart, errors and TTS', async () => {
  const saved = new Map(); global.sessionStorage = { getItem: k => saved.get(k), setItem: (k,v) => saved.set(k,v), removeItem: k => saved.delete(k) };
  const calls = []; const answer = 'السلام علیکم! Roman Urdu\n**CNIC**';
  global.fetch = async (url, init) => {
    calls.push({url, init});
    return new Response(JSON.stringify(url.endsWith('/sessions') ? {session_id:'same-session'} : {response:answer,sources:[{label:'Document',origin:'user_upload'}]}));
  };
  const api = load('services/api.ts', {'../data':{}, './client':load('services/client.ts')});
  const sessions = await Promise.all([api.createSession(), api.createSession()]);
  assert.equal(calls.length,1); assert.equal(sessions[0].id,sessions[1].id);
  const result = await api.sendChatMessage({sessionId:sessions[0].id,message:'documents kya chahiye?',language:'ur'});
  assert.equal(result.response,answer); assert.equal(result.sources[0].kind,'upload');
  assert.deepEqual(JSON.parse(calls[1].init.body),{session_id:'same-session',message:'documents kya chahiye?'});
  await api.sendChatMessage({sessionId:sessions[0].id,message:'Explain this',upload:{file:new File(['sample'],'sample.pdf')}});
  assert.equal(calls[2].init.body.get('message'),'Explain this'); assert.equal(calls[2].init.body.get('file').name,'sample.pdf');
  assert.equal(calls[2].init.headers,undefined);
  global.fetch = async () => new Response('',{status:502});
  await assert.rejects(api.synthesizeSpeech('hello'),/provider/); assert.equal(result.response,answer);
  global.fetch = async () => { throw new TypeError('offline'); };
  await assert.rejects(api.checkHealth(),/Cannot reach/);
});
test('voice final transcript sends once; TTS failure only affects playback state', async () => {
  const states=[]; let rec; let sent=[];
  global.window={SpeechRecognition:class { constructor(){rec=this;} start(){} stop(){} abort(){} }};
  const react={useState: initial=>{const i=states.push(initial)-1;return [initial,v=>{states[i]=typeof v==='function'?v(states[i]):v;}];},useRef:current=>({current}),useEffect:fn=>{fn();}};
  const {useVoice}=load('services/useVoice.ts',{'react':react,'./api':{synthesizeSpeech:async()=>{throw new Error('TTS offline');}},'./voice':load('services/voice.ts')});
  const voice=useVoice(text=>sent.push(text),false);voice.listen();
  assert.equal(rec.lang,'en-PK');assert.equal(rec.continuous,false);assert.equal(rec.interimResults,true);
  rec.onresult({results:[{isFinal:false,0:{transcript:'CNIC'}}]});assert.equal(sent.length,0);
  const event={results:[{isFinal:true,0:{transcript:'CNIC renew kaise karun?'}}]};rec.onresult(event);rec.onresult(event);
  assert.deepEqual(sent,['CNIC renew kaise karun?']);
  await voice.speak('The full answer remains in chat.');
  assert.equal(states[0],'error');assert.match(states[1],/text answer is still available/);
});

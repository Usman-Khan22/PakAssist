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
  global.fetch = async (url, init) => {
    assert.ok(url.endsWith('/voice/tts'));
    assert.deepEqual(JSON.parse(init.body), {text:'Hello'});
    return new Response(new Uint8Array([82,73,70,70]), {headers:{'Content-Type':'audio/wav'}});
  };
  const speech = await api.synthesizeSpeech('Hello');
  assert.equal(speech.type, 'audio/wav');
  assert.deepEqual([...new Uint8Array(await speech.arrayBuffer())], [82,73,70,70]);
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

test('voice playback preserves the WAV Blob and releases its URL after playback', async () => {
  const states=[]; let player; let played=false; let received; let revoked;
  const blob = new Blob([new Uint8Array([82,73,70,70])], {type:'audio/wav'});
  const originalCreate = URL.createObjectURL; const originalRevoke = URL.revokeObjectURL;
  const originalAudio = global.Audio;
  URL.createObjectURL = value => {received=value; return 'blob:test-wav';};
  URL.revokeObjectURL = value => {revoked=value;};
  global.Audio = class {constructor(url){this.src=url;player=this;} async play(){played=true;} pause(){} };
  const react={useState: initial=>{const i=states.push(initial)-1;return [initial,v=>{states[i]=typeof v==='function'?v(states[i]):v;}];},useRef:current=>({current}),useEffect:fn=>{fn();}};
  try {
    const {useVoice}=load('services/useVoice.ts',{'react':react,'./api':{synthesizeSpeech:async()=>blob},'./voice':load('services/voice.ts')});
    const voice=useVoice(()=>{},false);
    await voice.speak('Hello from PakAssist.');
    assert.equal(received,blob); assert.equal(received.type,'audio/wav');
    assert.equal(player.src,'blob:test-wav'); assert.equal(played,true);
    player.onended(); assert.equal(revoked,'blob:test-wav'); assert.equal(states[0],'idle');
  } finally {
    URL.createObjectURL=originalCreate; URL.revokeObjectURL=originalRevoke; global.Audio=originalAudio;
  }
});

test('spoken summaries bound long prose and checklists without changing the answer', () => {
  const {makeVoiceFriendly} = load('services/voice.ts');
  const inputs = [
    'You can visit the service center ' + 'for assistance with your application '.repeat(80) + '.',
    'Required documents:\n' + Array.from({length:30},(_,i)=>`- Document ${i+1}: ${'supporting information '.repeat(10)}`).join('\n'),
    'First step. Second step! Third step? Fourth step. Fifth step.',
    'x'.repeat(1000),
  ];
  for (const fullAnswer of inputs) {
    const summary = makeVoiceFriendly(fullAnswer);
    assert.ok(summary.length > 0 && summary.length <= 500, `Unexpected length: ${summary.length}`);
    assert.ok((summary.match(/[.!?۔؟]+/g) || []).length <= 3, summary);
    assert.notEqual(summary, fullAnswer);
  }
  assert.equal(makeVoiceFriendly(''), '');
  assert.equal(makeVoiceFriendly('   '), '');
  assert.match(makeVoiceFriendly('You need your CNIC. Bring two photographs.'), /CNIC/);
  assert.match(makeVoiceFriendly('Aap ko apna CNIC chahiye. Do tasveerein saath le kar aayen.'), /Aap ko apna CNIC/);
  assert.match(makeVoiceFriendly('آپ کو اپنا شناختی کارڈ لانا ہوگا۔ دو تصاویر ساتھ لائیں۔'), /شناختی کارڈ/);
});

test('spoken office summaries omit contact details and source metadata', () => {
  const {makeVoiceFriendly} = load('services/voice.ts');
  const fullAnswer = [
    'I found these passport service centers for Islamabad:',
    ...Array.from({length:15},(_,i)=>[
      `${i+1}. Passport Center ${i+1}`,
      'Address: Building 123, Very Long Road, Sector G-10, Islamabad',
      'Phone: +92 51 1234567',
      'Hours: Monday to Friday, 9 am to 5 pm',
      'Source: https://example.gov.pk/offices',
      'Confidence: dataset_verified',
    ].join('\n')),
  ].join('\n');
  const summary = makeVoiceFriendly(fullAnswer);
  assert.ok(summary.length <= 500);
  assert.match(summary, /passport|Passport/);
  assert.doesNotMatch(summary, /Building 123|Very Long Road|1234567|Monday|https:|dataset_verified|Confidence|Source:/);
  assert.ok((summary.match(/Passport Center/g) || []).length <= 3);
});

test('spoken summaries retain amounts and omit localized office details', () => {
  const {makeVoiceFriendly} = load('services/voice.ts');
  assert.match(makeVoiceFriendly('The amount shown is Rs 1234.50. Please confirm it before paying.'), /1234\.50/);
  const roman = makeVoiceFriendly('Lahore ke liye yeh service centers mile hain:\n1. Liberty Center\nPata: 45 Main Boulevard\nPhone: 042-12345678\nBharosa: dataset_verified\nSource: https://example.gov.pk');
  assert.match(roman, /Lahore/);
  assert.doesNotMatch(roman, /Main Boulevard|12345678|dataset_verified|https:/);
  const urdu = makeVoiceFriendly('لاہور میں یہ مراکز ملے ہیں:\n1. لبرٹی مرکز\nپتہ: مین روڈ\nفون: 042-12345678\nاعتماد: dataset_verified\nماخذ: https://example.gov.pk');
  assert.match(urdu, /لاہور/);
  assert.doesNotMatch(urdu, /مین روڈ|12345678|dataset_verified|https:/);
});

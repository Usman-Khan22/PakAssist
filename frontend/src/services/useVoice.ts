import { useEffect, useRef, useState } from 'react';
import { synthesizeSpeech } from './api';
import { makeVoiceFriendly } from './voice';
interface Recognition {
  continuous: boolean; interimResults: boolean; lang: string;
  onresult: ((event: { results: { isFinal: boolean; 0: { transcript: string } }[] }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void; stop(): void; abort(): void;
}
type SpeechWindow = Window & { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
export function useVoice(onTranscript: (text: string) => void, busy: boolean) {
  const constructor = (window as SpeechWindow).SpeechRecognition || (window as SpeechWindow).webkitSpeechRecognition;
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const [transcript, setTranscript] = useState('');
  const recognition = useRef<Recognition | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  const url = useRef('');
  const generation = useRef(0);
  const mounted = useRef(true);
  const callback = useRef(onTranscript); callback.current = onTranscript;
  const stop = () => {
    generation.current++;
    if (recognition.current) { recognition.current.onend = null; recognition.current.onresult = null; recognition.current.onerror = null; recognition.current.abort(); recognition.current = null; }
    if (audio.current) { audio.current.pause(); audio.current.src = ''; audio.current = null; }
    if (url.current) { URL.revokeObjectURL(url.current); url.current = ''; }
    setStatus('idle');
  };
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; stop(); }; }, []);
  const speak = async (text: string) => {
    if (!mounted.current) return;
    stop(); setError(''); setStatus('speaking'); const token = generation.current;
    try {
      const blob = await synthesizeSpeech(makeVoiceFriendly(text).slice(0, 5000));
      if (token !== generation.current) return;
      url.current = URL.createObjectURL(blob); const player = new Audio(url.current); audio.current = player;
      player.onended = stop;
      player.onerror = () => { stop(); setStatus('error'); setError('Voice playback failed. The text answer is still available.'); };
      await player.play();
    } catch {
      if (token !== generation.current) return;
      stop(); setStatus('error'); setError('Voice playback failed. The text answer is still available.');
    }
  };
  const listen = () => {
    if (status === 'listening') { recognition.current?.stop(); return; }
    if (busy || !constructor) return;
    stop(); setError(''); setTranscript('');
    const rec = new constructor(); recognition.current = rec;
    rec.continuous = false; rec.interimResults = true; rec.lang = 'en-PK';
    let sent = false;
    rec.onresult = event => {
      const results = Array.from(event.results); const text = results.map(r => r[0].transcript).join(' ');
      setTranscript(text);
      if (!sent && results.length && results.every(r => r.isFinal) && text.trim()) {
        sent = true; setStatus('thinking'); rec.stop(); callback.current(text.trim());
      }
    };
    rec.onerror = event => { setStatus('error'); setError(event.error === 'not-allowed' || event.error === 'service-not-allowed' ? 'Microphone permission was denied. Allow microphone access or continue typing.' : 'Voice input failed. Please try again or continue typing.'); };
    rec.onend = () => { recognition.current = null; setStatus(current => current === 'listening' ? 'idle' : current); };
    try { setStatus('listening'); rec.start(); } catch { setStatus('error'); setError('Microphone could not be started. You can continue typing.'); }
  };
  return { status: !constructor && status === 'idle' ? 'unsupported' : status, error, transcript, listen, speak, stop };
}

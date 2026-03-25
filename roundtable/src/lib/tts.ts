// src/lib/tts.ts

export function isSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window;
}

export function loadVoices(): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    const voices = speechSynthesis.getVoices();
    if (voices.length > 0) {
      resolve(voices);
      return;
    }
    // Chrome loads voices asynchronously — wait for the event
    const timeout = setTimeout(() => {
      resolve(speechSynthesis.getVoices());
    }, 2000);
    speechSynthesis.addEventListener('voiceschanged', () => {
      clearTimeout(timeout);
      resolve(speechSynthesis.getVoices());
    }, { once: true });
  });
}

export async function assignVoices(count: number, language: 'en' | 'zh' = 'en'): Promise<SpeechSynthesisVoice[]> {
  if (!isSupported()) return [];
  const all = await loadVoices();
  const filtered = all.filter(v =>
    language === 'zh' ? v.lang.startsWith('zh') : v.lang.startsWith('en')
  );
  const pool = filtered.length >= count ? filtered : (all.length > 0 ? all : []);
  if (pool.length === 0) return [];
  // Space selections evenly across the pool for maximum variety
  return Array.from({ length: count }, (_, i) =>
    pool[Math.floor((i / count) * pool.length)]
  );
}

export function speak(text: string, voice: SpeechSynthesisVoice | undefined): void {
  if (!isSupported()) return;
  const utterance = new SpeechSynthesisUtterance(text);
  if (voice) utterance.voice = voice;
  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  // Native queue: multiple speak() calls play sequentially — do NOT cancel before calling
  speechSynthesis.speak(utterance);
}

// Only call from: (1) mute toggle, (2) useEffect unmount cleanup. Never before speak().
export function cancel(): void {
  if (!isSupported()) return;
  speechSynthesis.cancel();
}

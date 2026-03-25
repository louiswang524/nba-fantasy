import { chat, chatStream } from './llm';
import { Persona, Message, Purpose } from '@/types';

const PURPOSE_PROMPTS: Record<Purpose, string> = {
  'entertainment': 'Make the discussion engaging, witty, and entertaining.',
  'learning': 'Focus on educating and explaining concepts clearly.',
  'decision-making': 'Provide balanced analysis to help make informed decisions.',
};

function buildPrompt(
  topic: string,
  purpose: Purpose,
  personas: Persona[],
  messages: Message[],
  respondingPersona: Persona,
  language: 'en' | 'zh' = 'en'
): { systemPrompt: string; userMessage: string } {
  const recentMessages = messages.slice(-6);
  const context = recentMessages
    .map(m => `${m.role === 'persona' ? m.personaName : m.role === 'guest' ? 'Guest' : 'User'}: ${m.content}`)
    .join('\n');

  let systemPrompt = `You are ${respondingPersona.name}, ${respondingPersona.title}.
Background: ${respondingPersona.background}
Expertise: ${respondingPersona.expertise.join(', ')}
Perspective: ${respondingPersona.perspective}

You are part of a roundtable discussion about "${topic}".
${PURPOSE_PROMPTS[purpose]}

Speak in your persona's voice. Be concise (2-4 sentences). Respond to the discussion flow.

Personas in the discussion:
${personas.map(p => `- ${p.name} (${p.title}): ${p.perspective}`).join('\n')}`;

  if (language === 'zh') {
    systemPrompt += '\nRespond entirely in Simplified Chinese (简体中文).';
  }

  const userMessage = messages.length === 0
    ? `Start the discussion about "${topic}". Provide an opening statement.`
    : `Continue the discussion. Respond to the latest messages:\n${context}`;

  return { systemPrompt, userMessage };
}

export async function generateDiscussionTurn(
  topic: string,
  purpose: Purpose,
  personas: Persona[],
  messages: Message[],
  respondingPersona: Persona
): Promise<string> {
  const { systemPrompt, userMessage } = buildPrompt(topic, purpose, personas, messages, respondingPersona);
  const response = await chat([
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userMessage },
  ]);
  return response.content || 'I need to think about this more.';
}

export async function generateDiscussionTurnStream(
  topic: string,
  purpose: Purpose,
  personas: Persona[],
  messages: Message[],
  respondingPersona: Persona,
  language: 'en' | 'zh' = 'en'
): Promise<ReadableStream<Uint8Array>> {
  const { systemPrompt, userMessage } = buildPrompt(topic, purpose, personas, messages, respondingPersona, language);
  return chatStream([
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userMessage },
  ]);
}

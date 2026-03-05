import { openai } from './openai';
import { Persona, Message, Purpose } from '@/types';

const PURPOSE_PROMPTS: Record<Purpose, string> = {
  'entertainment': 'Make the discussion engaging, witty, and entertaining.',
  'learning': 'Focus on educating and explaining concepts clearly.',
  'decision-making': 'Provide balanced analysis to help make informed decisions.',
};

export async function generateDiscussionTurn(
  topic: string,
  purpose: Purpose,
  personas: Persona[],
  messages: Message[],
  respondingPersona: Persona
): Promise<string> {
  const purposePrompt = PURPOSE_PROMPTS[purpose];
  
  const recentMessages = messages.slice(-6);
  
  const context = recentMessages
    .map(m => `${m.role === 'persona' ? m.personaName : m.role === 'guest' ? 'Guest' : 'User'}: ${m.content}`)
    .join('\n');

  const systemPrompt = `You are ${respondingPersona.name}, ${respondingPersona.title}.
Background: ${respondingPersona.background}
Expertise: ${respondingPersona.expertise.join(', ')}
Perspective: ${respondingPersona.perspective}

You are part of a roundtable discussion about "${topic}".
${purposePrompt}

Speak in your persona's voice. Be concise (2-4 sentences). Respond to the discussion flow.

Personas in the discussion:
${personas.map(p => `- ${p.name} (${p.title}): ${p.perspective}`).join('\n')}`;

  const userMessage = messages.length === 0 
    ? `Start the discussion about "${topic}". Provide an opening statement.`
    : `Continue the discussion. Respond to the latest messages:\n${context}`;

  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userMessage },
    ],
  });

  return response.choices[0]?.message?.content || 'I need to think about this more.';
}

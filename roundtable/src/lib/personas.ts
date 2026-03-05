import { chat, getProvider } from './llm';
import { Persona, Purpose } from '@/types';

const PERSPECTIVES: Persona['perspective'][] = ['optimist', 'skeptic', 'realist', 'researcher', 'practitioner', 'critic'];

function getRandomPerspectives(count: number): Persona['perspective'][] {
  const shuffled = [...PERSPECTIVES].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

export async function generatePersonas(topic: string, purpose: Purpose, count: number = 4): Promise<Persona[]> {
  const perspectives = getRandomPerspectives(count);
  const provider = getProvider();
  
  const systemPrompt = `You are a persona generator. Generate ${count} diverse expert personas for discussing "${topic}" with purpose "${purpose}".
  
Return a JSON array with exactly ${count} personas. Each persona must have:
- id: unique string (e.g., "persona-1")
- name: realistic full name
- title: professional title relevant to ${topic}
- background: 1-2 sentence background
- expertise: array of 2-3 expertise areas
- perspective: one of: ${perspectives.join(', ')}

Generate diverse, realistic personas that would have genuine influence in "${topic}". ${
    provider === 'gemini' ? 'IMPORTANT: Output ONLY valid JSON, no markdown formatting.' : ''
  }`;

  const response = await chat([
    { role: 'system', content: systemPrompt },
    { role: 'user', content: `Generate personas for topic: ${topic}` },
  ]);

  const content = response.content;
  if (!content) {
    throw new Error('Failed to generate personas');
  }

  const parsed = JSON.parse(content);
  const personas = Array.isArray(parsed) ? parsed : parsed.personas || [];
  
  return personas.map((p: Partial<Persona>, i: number) => ({
    id: `persona-${i + 1}`,
    name: p.name || 'Expert',
    title: p.title || 'Specialist',
    background: p.background || '',
    expertise: p.expertise || [],
    perspective: perspectives[i],
  }));
}

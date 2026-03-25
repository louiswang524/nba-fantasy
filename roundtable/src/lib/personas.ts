import { chat, getProvider } from './llm';
import { Persona, Purpose } from '@/types';

const PERSPECTIVES: Persona['perspective'][] = ['optimist', 'skeptic', 'realist', 'researcher', 'practitioner', 'critic'];

function getRandomPerspectives(count: number): Persona['perspective'][] {
  const shuffled = [...PERSPECTIVES].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

function parseJSON(content: string): any {
  const trimmed = content.trim();
  const jsonMatch = trimmed.match(/```json\n([\s\S]*?)\n```/) ||
                   trimmed.match(/```\n([\s\S]*?)\n```/) ||
                   trimmed.match(/\[[\s\S]*\]/);

  if (jsonMatch) {
    try {
      return JSON.parse(jsonMatch[1] || jsonMatch[0]);
    } catch {
      return JSON.parse(trimmed);
    }
  }
  return JSON.parse(trimmed);
}

export async function generatePersonas(topic: string, purpose: Purpose, count: number = 4, names?: string[], language: 'en' | 'zh' = 'en'): Promise<Persona[]> {
  const perspectives = getRandomPerspectives(Math.max(count, names?.length ?? 0));
  const provider = getProvider();
  const personaCount = names && names.length > 0 ? names.length : count;

  const selectionInstruction = names && names.length > 0
    ? `Use exactly these people (in this order): ${names.join(', ')}.`
    : `Select ${count} real people who have meaningful, documented views on this topic.
Maximize diversity across:
- Time period: mix ancient, medieval, early modern, and contemporary figures
- Culture and geography: avoid defaulting to Western or American voices only
- Discipline: thinkers, scientists, practitioners, artists, leaders
- Viewpoint: include people who would genuinely disagree with each other`;

  let systemPrompt = `You are curating a Time Machine Roundtable — a discussion where real people from any era meet to debate a topic.

${selectionInstruction}

For each person, generate their roundtable profile grounded in their actual documented views, writings, and known positions.

Return a JSON array with exactly ${personaCount} objects:
[{
  "id": "persona-1",
  "name": "full name",
  "title": "their actual historical or professional title",
  "background": "2-3 sentences on their real documented positions relevant to the topic — cite actual works, quotes, or known stances",
  "expertise": ["area1", "area2", "area3"],
  "perspective": "one of: ${perspectives.join(', ')}"
}]

${provider === 'gemini' ? 'Output ONLY valid JSON, no markdown.' : ''}`;

  if (language === 'zh') {
    systemPrompt += '\nRespond entirely in Simplified Chinese (简体中文).';
  }

  const response = await chat([
    { role: 'system', content: systemPrompt },
    { role: 'user', content: `Topic: "${topic}"\nPurpose: ${purpose}` },
  ]);

  if (!response.content) throw new Error('Failed to generate personas');

  try {
    const parsed = parseJSON(response.content);
    const personas = Array.isArray(parsed) ? parsed : parsed.personas || [];

    return personas.map((p: Partial<Persona>, i: number) => ({
      id: `persona-${i + 1}`,
      name: p.name || names?.[i] || 'Expert',
      title: p.title || 'Specialist',
      background: p.background || '',
      expertise: p.expertise || [],
      perspective: perspectives[i % perspectives.length],
    }));
  } catch (e) {
    console.error('Failed to parse personas:', e);
    throw new Error('Failed to parse personas');
  }
}

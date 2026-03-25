import { NextRequest, NextResponse } from 'next/server';
import { createSession, updateSession } from '@/lib/sessions';
import { generatePersonas } from '@/lib/personas';

export async function POST(request: NextRequest) {
  try {
    const { topic, purpose, people, language } = await request.json();

    if (!topic || !purpose) {
      return NextResponse.json({ error: 'Missing topic or purpose' }, { status: 400 });
    }

    const lang: 'en' | 'zh' = language === 'zh' ? 'zh' : 'en';
    const names: string[] | undefined = Array.isArray(people) && people.length > 0 ? people : undefined;

    const session = createSession(topic, purpose, lang);
    const personas = await generatePersonas(topic, purpose as any, 4, names, lang);

    updateSession(session.id, { personas });

    return NextResponse.json({ session: { ...session, personas } });
  } catch (error) {
    console.error('Error creating session:', error);
    return NextResponse.json({ error: 'Failed to create session' }, { status: 500 });
  }
}

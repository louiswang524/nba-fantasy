import { NextRequest } from 'next/server';
import { getSession } from '@/lib/sessions';
import { generateSummaryStream } from '@/lib/chat';

export async function POST(request: NextRequest) {
  try {
    const { sessionId } = await request.json();

    const session = getSession(sessionId);
    if (!session) {
      return new Response(JSON.stringify({ error: 'Session not found' }), { status: 404 });
    }

    const language = (session.language ?? 'en') as 'en' | 'zh';

    const stream = await generateSummaryStream(
      session.topic,
      session.personas,
      session.messages,
      language
    );

    return new Response(stream, {
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  } catch (error) {
    console.error('Error generating summary:', error);
    return new Response(JSON.stringify({ error: 'Failed to generate summary' }), { status: 500 });
  }
}

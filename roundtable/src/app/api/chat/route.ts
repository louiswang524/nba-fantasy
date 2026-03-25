import { NextRequest } from 'next/server';
import { getSession, updateSession } from '@/lib/sessions';
import { generateDiscussionTurnStream } from '@/lib/chat';

export async function POST(request: NextRequest) {
  try {
    const { sessionId, guestMessage } = await request.json();

    const session = getSession(sessionId);
    if (!session) {
      return new Response(JSON.stringify({ error: 'Session not found' }), { status: 404 });
    }

    let messages = session.messages;
    const personas = session.personas;

    if (guestMessage) {
      messages = [...messages, {
        id: `msg-${Date.now()}`,
        role: 'guest' as const,
        content: guestMessage,
        timestamp: Date.now(),
      }];
    }

    const messageCount = messages.filter(m => m.role === 'persona').length;
    const personaIndex = messageCount % personas.length;
    const respondingPersona = personas[personaIndex];
    const messageId = `msg-${Date.now()}`;

    const language = (session.language ?? 'en') as 'en' | 'zh';

    const llmStream = await generateDiscussionTurnStream(
      session.topic,
      session.purpose,
      personas,
      messages,
      respondingPersona,
      language
    );

    // Accumulate full content to save to session once stream closes
    let fullContent = '';
    const saveOnClose = new TransformStream<Uint8Array, Uint8Array>({
      transform(chunk, controller) {
        fullContent += new TextDecoder().decode(chunk);
        controller.enqueue(chunk);
      },
      flush() {
        const personaMsg = {
          id: messageId,
          role: 'persona' as const,
          personaId: respondingPersona.id,
          personaName: respondingPersona.name,
          perspective: respondingPersona.perspective,
          content: fullContent || 'I need to think about this more.',
          timestamp: Date.now(),
        };
        updateSession(sessionId, { messages: [...messages, personaMsg] });
      },
    });

    // HTTP headers must be ASCII — strip non-ASCII chars from LLM-generated values
    const toHeader = (s: string) => s.replace(/[^\x20-\x7E]/g, '');

    return new Response(llmStream.pipeThrough(saveOnClose), {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'X-Persona-Id': toHeader(respondingPersona.id),
        'X-Persona-Name': toHeader(respondingPersona.name),
        'X-Persona-Title': toHeader(respondingPersona.title),
        'X-Persona-Perspective': toHeader(respondingPersona.perspective),
        'X-Message-Id': toHeader(messageId),
      },
    });
  } catch (error) {
    console.error('Error in chat:', error);
    return new Response(JSON.stringify({ error: 'Failed to generate response' }), { status: 500 });
  }
}

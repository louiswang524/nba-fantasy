import { NextRequest, NextResponse } from 'next/server';
import { getSession, updateSession } from '@/lib/sessions';
import { generateDiscussionTurn } from '@/lib/chat';

export async function POST(request: NextRequest) {
  try {
    const { sessionId, guestMessage } = await request.json();
    
    const session = getSession(sessionId);
    if (!session) {
      return NextResponse.json({ error: 'Session not found' }, { status: 404 });
    }

    let messages = session.messages;
    const personas = session.personas;

    if (guestMessage) {
      const guestMsg = {
        id: `msg-${Date.now()}`,
        role: 'guest' as const,
        content: guestMessage,
        timestamp: Date.now(),
      };
      messages = [...messages, guestMsg];
    }

    const messageCount = messages.filter(m => m.role === 'persona').length;
    const personaIndex = messageCount % personas.length;
    const respondingPersona = personas[personaIndex];

    const content = await generateDiscussionTurn(
      session.topic,
      session.purpose,
      personas,
      messages,
      respondingPersona
    );

    const personaMsg = {
      id: `msg-${Date.now()}`,
      role: 'persona' as const,
      personaId: respondingPersona.id,
      personaName: respondingPersona.name,
      content,
      timestamp: Date.now(),
    };

    messages = [...messages, personaMsg];
    updateSession(sessionId, { messages });

    return NextResponse.json({ 
      message: personaMsg,
      persona: respondingPersona,
    });
  } catch (error) {
    console.error('Error in chat:', error);
    return NextResponse.json({ error: 'Failed to generate response' }, { status: 500 });
  }
}

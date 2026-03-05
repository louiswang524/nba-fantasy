import { Session } from '@/types';

const sessions = new Map<string, Session>();

export function createSession(topic: string, purpose: string): Session {
  const session: Session = {
    id: `session-${Date.now()}`,
    topic,
    purpose: purpose as Session['purpose'],
    personas: [],
    messages: [],
    createdAt: Date.now(),
  };
  sessions.set(session.id, session);
  return session;
}

export function getSession(id: string): Session | undefined {
  return sessions.get(id);
}

export function updateSession(id: string, updates: Partial<Session>): Session | undefined {
  const session = sessions.get(id);
  if (!session) return undefined;
  
  const updated = { ...session, ...updates };
  sessions.set(id, updated);
  return updated;
}

'use client';

import { useState } from 'react';
import { TopicForm } from '@/components/TopicForm';
import { ChatInterface } from '@/components/ChatInterface';
import { Persona, Purpose, Session } from '@/types';

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [turns, setTurns] = useState<number>(12);

  const handleStart = async (topic: string, purpose: Purpose, people: string[], turns: number) => {
    setTurns(turns);
    setIsLoading(true);
    try {
      const res = await fetch('/api/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, purpose, people }),
      });

      const data = await res.json();
      setSession(data.session);
    } catch (error) {
      console.error('Error starting session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewTopic = () => {
    setSession(null);
  };

  if (!session) {
    return <TopicForm onSubmit={handleStart} isLoading={isLoading} />;
  }

  return (
    <ChatInterface
      sessionId={session.id}
      topic={session.topic}
      purpose={session.purpose}
      initialPersonas={session.personas}
      onNewTopic={handleNewTopic}
      turns={turns}
    />
  );
}

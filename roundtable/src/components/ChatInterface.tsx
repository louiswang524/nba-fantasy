'use client';

import { useState, useRef, useEffect } from 'react';
import { Message, Persona, Purpose } from '@/types';
import { MessageBubble } from './MessageBubble';
import { SidePanel } from './SidePanel';

interface ChatInterfaceProps {
  sessionId: string;
  topic: string;
  purpose: Purpose;
  initialPersonas: Persona[];
  onNewTopic: () => void;
}

export function ChatInterface({ 
  sessionId, 
  topic, 
  purpose, 
  initialPersonas,
  onNewTopic 
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [personas, setPersonas] = useState<Persona[]>(initialPersonas);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (guestMessage?: string) => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, guestMessage }),
      });
      
      const data = await res.json();
      if (data.message) {
        setMessages(prev => [...prev, data.message]);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      <div className="flex-1 flex flex-col">
        <header className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-800">{topic}</h1>
              <p className="text-sm text-gray-500 capitalize">{purpose.replace('-', ' ')}</p>
            </div>
            <button
              onClick={onNewTopic}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              New Topic
            </button>
          </div>
          <div className="mt-2 flex gap-2">
            {personas.map(p => (
              <span key={p.id} className="text-xs bg-gray-100 px-2 py-1 rounded">
                {p.name}
              </span>
            ))}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-8">
              <p>The discussion is starting...</p>
            </div>
          )}
          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && (
            <div className="text-center text-gray-400 text-sm">
              <span className="animate-pulse">Thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <SidePanel onSend={sendMessage} isLoading={isLoading} />
    </div>
  );
}

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

  useEffect(() => {
    if (sessionId && messages.length === 0 && !isLoading) {
      startDiscussion();
    }
  }, [sessionId]);

  const startDiscussion = async () => {
    setIsLoading(true);
    const turns = 4;
    for (let i = 0; i < turns; i++) {
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sessionId, guestMessage: null }),
        });
        
        const data = await res.json();
        if (data.message) {
          setMessages(prev => [...prev, data.message]);
        }
      } catch (error) {
        console.error('Error:', error);
        break;
      }
    }
    setIsLoading(false);
  };

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

  const getPurposeLabel = (p: Purpose) => {
    switch (p) {
      case 'entertainment': return '🎭 Entertainment';
      case 'learning': return '📚 Learning';
      case 'decision-making': return '🎯 Decision Making';
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="flex-1 flex flex-col">
        <header className="bg-white/5 backdrop-blur-xl border-b border-white/10 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">{topic}</h1>
              <p className="text-sm text-violet-400 mt-1">{getPurposeLabel(purpose)}</p>
            </div>
            <button
              onClick={onNewTopic}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-sm font-medium rounded-lg transition-all duration-200 border border-white/10 hover:border-white/20"
            >
              + New Discussion
            </button>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <span className="text-slate-400 text-sm">Experts:</span>
            <div className="flex flex-wrap gap-2">
              {personas.map((p, idx) => (
                <div 
                  key={p.id} 
                  className="flex items-center gap-2 bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 px-3 py-1.5 rounded-full border border-violet-500/30"
                >
                  <div className={`w-2 h-2 rounded-full ${
                    ['bg-emerald-400', 'bg-amber-400', 'bg-cyan-400', 'bg-rose-400'][idx % 4]
                  }`} />
                  <span className="text-sm text-white font-medium">{p.name}</span>
                  <span className="text-xs text-slate-400">•</span>
                  <span className="text-xs text-slate-400 capitalize">{p.perspective}</span>
                </div>
              ))}
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center mb-4 shadow-2xl shadow-violet-500/30 animate-pulse">
                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <p className="text-slate-400 text-lg">The discussion is starting...</p>
              <p className="text-slate-500 text-sm mt-2">Experts are joining the roundtable</p>
            </div>
          )}
          {messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && (
            <div className="flex items-center gap-3 text-slate-400">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-sm">Thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <SidePanel onSend={sendMessage} isLoading={isLoading} />
    </div>
  );
}

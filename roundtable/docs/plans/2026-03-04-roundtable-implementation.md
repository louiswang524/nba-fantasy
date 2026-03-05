# Roundtable Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** A chat-style web app where users input a topic, and 3-5 AI personas discuss it. Users can inject comments via a side panel.

**Architecture:** Next.js app with API routes for backend. Single-page chat interface with collapsible side panel. OpenAI API for LLM-powered persona responses.

**Tech Stack:** Next.js, React, Tailwind CSS, OpenAI SDK, TypeScript

---

## Task 1: Initialize Next.js Project

**Files:**
- Create: `package.json`
- Create: `next.config.js`
- Create: `tsconfig.json`
- Create: `tailwind.config.js`
- Create: `postcss.config.js`
- Create: `app/layout.tsx`
- Create: `app/globals.css`

**Step 1: Create project structure**

```bash
npx create-next-app@latest roundtable --typescript --tailwind --eslint --app --src-dir --no-import-alias
```

**Step 2: Install dependencies**

```bash
npm install openai
```

**Step 3: Commit**

```bash
git add .
git commit -m "chore: initialize Next.js project with TypeScript and Tailwind"
```

---

## Task 2: Configure Environment

**Files:**
- Create: `.env.local`

**Step 1: Create environment file**

```
OPENAI_API_KEY=your-api-key-here
```

**Step 2: Create .env.example**

```
OPENAI_API_KEY=
```

**Step 3: Commit**

```bash
git add .env.local .env.example
git commit -m "chore: add environment configuration"
```

---

## Task 3: Define TypeScript Types

**Files:**
- Create: `src/types/index.ts`

**Step 1: Write types**

```typescript
export type Purpose = 'entertainment' | 'learning' | 'decision-making';

export interface Persona {
  id: string;
  name: string;
  title: string;
  background: string;
  expertise: string[];
  perspective: 'optimist' | 'skeptic' | 'realist' | 'researcher' | 'practitioner';
}

export interface Message {
  id: string;
  role: 'persona' | 'user' | 'guest';
  personaId?: string;
  personaName?: string;
  content: string;
  timestamp: number;
}

export interface Session {
  id: string;
  topic: string;
  purpose: Purpose;
  personas: Persona[];
  messages: Message[];
  createdAt: number;
}
```

**Step 2: Commit**

```bash
git add src/types/index.ts
git commit -m "feat: add TypeScript types for personas, messages, sessions"
```

---

## Task 4: Create OpenAI Client Utility

**Files:**
- Create: `src/lib/openai.ts`

**Step 1: Write utility**

```typescript
import OpenAI from 'openai';

export const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});
```

**Step 2: Commit**

```bash
git add src/lib/openai.ts
git commit -m "feat: add OpenAI client utility"
```

---

## Task 5: Create Persona Generation Service

**Files:**
- Create: `src/lib/personas.ts`

**Step 1: Write service**

```typescript
import { openai } from './openai';
import { Persona, Purpose } from '@/types';

const PERSPECTIVES = ['optimist', 'skeptic', 'realist', 'researcher', 'practitioner', 'critic'];

function getRandomPerspectives(count: number): Persona['perspective'][] {
  const shuffled = [...PERSPECTIVES].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

export async function generatePersonas(topic: string, purpose: Purpose, count: number = 4): Promise<Persona[]> {
  const perspectives = getRandomPerspectives(count);
  
  const systemPrompt = `You are a persona generator. Generate ${count} diverse expert personas for discussing "${topic}" with purpose "${purpose}".
  
Return a JSON array with exactly ${count} personas. Each persona must have:
- id: unique string (e.g., "persona-1")
- name: realistic full name
- title: professional title relevant to ${topic}
- background: 1-2 sentence background
- expertise: array of 2-3 expertise areas
- perspective: one of: ${perspectives.join(', ')}

Generate diverse, realistic personas that would have genuine influence in "${topic}".`;

  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: `Generate personas for topic: ${topic}` },
    ],
    response_format: { type: 'json_object' },
  });

  const content = response.choices[0]?.message?.content;
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
```

**Step 2: Commit**

```bash
git add src/lib/personas.ts
git commit -m "feat: add persona generation service"
```

---

## Task 6: Create Chat/Discussion Service

**Files:**
- Create: `src/lib/chat.ts`

**Step 1: Write service**

```typescript
import { openai } from './openai';
import { Persona, Message, Purpose } from '@/types';

const PURPOSE_PROMPTS: Record<Purpose, string> = {
  'entertainment': 'Make the discussion engaging, witty, and entertaining.',
  'learning': 'Focus on educating and explaining concepts clearly.',
  'decision-making': 'Provide balanced analysis to help make informed decisions.',
};

export async function generateDiscussionTurn(
  topic: string,
  purpose: Purpose,
  personas: Persona[],
  messages: Message[],
  respondingPersona: Persona
): Promise<string> {
  const purposePrompt = PURPOSE_PROMPTS[purpose];
  
  const recentMessages = messages.slice(-6);
  
  const context = recentMessages
    .map(m => `${m.role === 'persona' ? m.personaName : m.role === 'guest' ? 'Guest' : 'User'}: ${m.content}`)
    .join('\n');

  const systemPrompt = `You are ${respondingPersona.name}, ${respondingPersona.title}.
Background: ${respondingPersona.background}
Expertise: ${respondingPersona.expertise.join(', ')}
Perspective: ${respondingPersona.perspective}

You are part of a roundtable discussion about "${topic}".
${purposePrompt}

Speak in your persona's voice. Be concise (2-4 sentences). Respond to the discussion flow.

Personas in the discussion:
${personas.map(p => `- ${p.name} (${p.title}): ${p.perspective}`).join('\n')}`;

  const userMessage = messages.length === 0 
    ? `Start the discussion about "${topic}". Provide an opening statement.`
    : `Continue the discussion. Respond to the latest messages:\n${context}`;

  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userMessage },
    ],
  });

  return response.choices[0]?.message?.content || 'I need to think about this more.';
}
```

**Step 2: Commit**

```bash
git add src/lib/chat.ts
git commit -m "feat: add discussion generation service"
```

---

## Task 7: Create Session Store (In-Memory)

**Files:**
- Create: `src/lib/sessions.ts`

**Step 1: Write store**

```typescript
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
```

**Step 2: Commit**

```bash
git add src/lib/sessions.ts
git commit -m "feat: add in-memory session store"
```

---

## Task 8: Create API Routes

**Files:**
- Create: `app/api/session/route.ts`
- Create: `app/api/chat/route.ts`

**Step 1: Create session route**

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { createSession, updateSession } from '@/lib/sessions';
import { generatePersonas } from '@/lib/personas';

export async function POST(request: NextRequest) {
  try {
    const { topic, purpose } = await request.json();
    
    if (!topic || !purpose) {
      return NextResponse.json({ error: 'Missing topic or purpose' }, { status: 400 });
    }

    const session = createSession(topic, purpose);
    const personas = await generatePersonas(topic, purpose as any);
    
    updateSession(session.id, { personas });
    
    return NextResponse.json({ session: { ...session, personas } });
  } catch (error) {
    console.error('Error creating session:', error);
    return NextResponse.json({ error: 'Failed to create session' }, { status: 500 });
  }
}
```

**Step 2: Create chat route**

```typescript
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
    let personas = session.personas;

    // If guest message, add it first
    if (guestMessage) {
      const guestMsg = {
        id: `msg-${Date.now()}`,
        role: 'guest' as const,
        content: guestMessage,
        timestamp: Date.now(),
      };
      messages = [...messages, guestMsg];
    }

    // Get next persona to respond
    const messageCount = messages.filter(m => m.role === 'persona').length;
    const personaIndex = messageCount % personas.length;
    const respondingPersona = personas[personaIndex];

    // Generate response
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
```

**Step 3: Commit**

```bash
git add app/api/session/route.ts app/api/chat/route.ts
git commit -m "feat: add session and chat API routes"
```

---

## Task 9: Create UI Components

**Files:**
- Create: `src/components/TopicForm.tsx`
- Create: `src/components/ChatInterface.tsx`
- Create: `src/components/MessageBubble.tsx`
- Create: `src/components/SidePanel.tsx`

**Step 1: Create TopicForm**

```typescript
'use client';

import { useState } from 'react';
import { Purpose } from '@/types';

interface TopicFormProps {
  onSubmit: (topic: string, purpose: Purpose) => void;
  isLoading: boolean;
}

export function TopicForm({ onSubmit, isLoading }: TopicFormProps) {
  const [topic, setTopic] = useState('');
  const [purpose, setPurpose] = useState<Purpose>('learning');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim()) {
      onSubmit(topic.trim(), purpose);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6 text-gray-800">Roundtable</h1>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            What topic would you like to discuss?
          </label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., The future of AI in healthcare"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Purpose
          </label>
          <select
            value={purpose}
            onChange={(e) => setPurpose(e.target.value as Purpose)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          >
            <option value="entertainment">Entertainment</option>
            <option value="learning">Learning</option>
            <option value="decision-making">Decision Making</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={isLoading || !topic.trim()}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Starting...' : 'Start Discussion'}
        </button>
      </form>
    </div>
  );
}
```

**Step 2: Create MessageBubble**

```typescript
import { Message } from '@/types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isPersona = message.role === 'persona';
  const isGuest = message.role === 'guest';

  return (
    <div className={`mb-4 ${isGuest ? 'ml-auto max-w-[80%]' : ''}`}>
      <div className={`p-4 rounded-lg ${
        isPersona 
          ? 'bg-blue-50 border border-blue-100' 
          : isGuest 
            ? 'bg-green-50 border border-green-100'
            : 'bg-gray-50'
      }`}>
        {isPersona && (
          <div className="text-sm font-medium text-blue-600 mb-1">
            {message.personaName}
          </div>
        )}
        {isGuest && (
          <div className="text-sm font-medium text-green-600 mb-1">
            Guest
          </div>
        )}
        <p className="text-gray-800 whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}
```

**Step 3: Create SidePanel**

```typescript
'use client';

import { useState } from 'react';

interface SidePanelProps {
  onSend: (message: string) => void;
  isLoading: boolean;
}

export function SidePanel({ onSend, isLoading }: SidePanelProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSend(message.trim());
      setMessage('');
    }
  };

  return (
    <div className="w-80 border-l border-gray-200 bg-gray-50 p-4 flex flex-col">
      <h2 className="font-semibold text-gray-700 mb-4">Join the Discussion</h2>
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Share your thoughts..."
          className="flex-1 w-full p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-green-500 focus:border-transparent mb-3"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !message.trim()}
          className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50"
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
```

**Step 4: Create ChatInterface**

```typescript
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
```

**Step 5: Commit**

```bash
git add src/components/TopicForm.tsx src/components/ChatInterface.tsx src/components/MessageBubble.tsx src/components/SidePanel.tsx
git commit -m "feat: add UI components"
```

---

## Task 10: Create Main Page

**Files:**
- Modify: `app/page.tsx`

**Step 1: Write main page**

```typescript
'use client';

import { useState } from 'react';
import { TopicForm } from '@/components/TopicForm';
import { ChatInterface } from '@/components/ChatInterface';
import { Persona, Purpose, Session } from '@/types';

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleStart = async (topic: string, purpose: Purpose) => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, purpose }),
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
    />
  );
}
```

**Step 2: Commit**

```bash
git add app/page.tsx
git commit -f "feat: add main page with session handling"
```

---

## Task 11: Test and Verify

**Step 1: Build the project**

```bash
npm run build
```

Expected: No errors

**Step 2: Start dev server**

```bash
npm run dev
```

**Step 3: Test manually**
1. Open http://localhost:3000
2. Enter a topic (e.g., "AI ethics")
3. Select purpose (e.g., "learning")
4. Click "Start Discussion"
5. Verify personas are generated
6. Watch discussion unfold
7. Type in side panel
8. Verify response

**Step 4: Commit**

```bash
git add .
git commit -m "feat: complete Roundtable app"
```

---

## Plan Complete

**All tasks complete!** The app should now:
- Accept topic + purpose input
- Generate 4 diverse AI personas
- Run a roundtable discussion
- Allow user to inject comments via side panel

**Next steps:**
- Add streaming for real-time responses
- Add loading states
- Improve persona selection logic
- Add error handling UI
- Consider user accounts later

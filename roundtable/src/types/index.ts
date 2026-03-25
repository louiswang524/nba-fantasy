export type Purpose = 'entertainment' | 'learning' | 'decision-making';

export interface Persona {
  id: string;
  name: string;
  title: string;
  background: string;
  expertise: string[];
  perspective: 'optimist' | 'skeptic' | 'realist' | 'researcher' | 'practitioner' | 'critic';
}

export interface Message {
  id: string;
  role: 'persona' | 'user' | 'guest';
  personaId?: string;
  personaName?: string;
  perspective?: string;
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
  language: 'en' | 'zh';
}

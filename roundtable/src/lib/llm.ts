import OpenAI from 'openai';
import Anthropic from '@anthropic-ai/sdk';
import { GoogleGenerativeAI } from '@google/generative-ai';
import fs from 'fs';
import path from 'path';

interface Config {
  provider: 'openai' | 'anthropic' | 'gemini';
  model: string;
}

function loadConfig(): Config {
  const configPath = path.join(process.cwd(), 'config.json');
  const content = fs.readFileSync(configPath, 'utf-8');
  return JSON.parse(content);
}

const config = loadConfig();

let openai: OpenAI | null = null;
let anthropic: Anthropic | null = null;
let gemini: GoogleGenerativeAI | null = null;

if (config.provider === 'openai') {
  openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
} else if (config.provider === 'anthropic') {
  anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
} else if (config.provider === 'gemini') {
  gemini = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');
}

export interface ChatMessage {
  role: 'system' | 'user';
  content: string;
}

export interface ChatResponse {
  content: string;
}

export async function chat(messages: ChatMessage[]): Promise<ChatResponse> {
  if (config.provider === 'openai' && openai) {
    const response = await openai.chat.completions.create({
      model: config.model,
      messages: messages as any,
    });
    return { content: response.choices[0]?.message?.content || '' };
  }

  if (config.provider === 'anthropic' && anthropic) {
    const systemMessage = messages.find(m => m.role === 'system');
    const userMessages = messages.filter(m => m.role === 'user');
    
    const response = await anthropic.messages.create({
      model: config.model,
      system: systemMessage?.content,
      messages: userMessages as any,
      max_tokens: 1024,
    });
    
    const textContent = response.content.find(c => c.type === 'text');
    return { content: textContent?.type === 'text' ? textContent.text : '' };
  }

  if (config.provider === 'gemini' && gemini) {
    const model = gemini.getGenerativeModel({ model: config.model });
    
    let prompt = '';
    for (const msg of messages) {
      if (msg.role === 'system') {
        prompt += `System: ${msg.content}\n`;
      } else {
        prompt += `User: ${msg.content}\n`;
      }
    }
    
    const result = await model.generateContent(prompt);
    const response = result.response;
    return { content: response.text() || '' };
  }

  throw new Error(`Provider ${config.provider} not configured properly`);
}

export function getProvider(): string {
  return config.provider;
}

export function getModel(): string {
  return config.model;
}

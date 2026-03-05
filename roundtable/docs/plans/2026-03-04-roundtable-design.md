# Roundtable - AI Persona Discussion Platform

**Date:** 2026-03-04  
**Status:** Approved

## Overview

A chat-style web app where users input a topic and purpose. The app creates 3-5 AI personas (simulating influential experts in that domain) who discuss the topic. Users observe the discussion and can inject comments via a side panel.

## Core Features

1. **Topic Input** - User enters a topic + selects purpose (entertainment, learning, decision making)
2. **Persona Generation** - AI generates 3-5 domain experts with different backgrounds, perspectives, and expertise
3. **Roundtable Discussion** - Personas discuss the topic in a multi-turn conversation
4. **User Participation** - Side panel allows user to inject comments into the discussion
5. **Streaming Responses** - Real-time streaming of AI responses for engaging UX

## User Flow

1. Landing page: Topic input form + purpose dropdown
2. User submits → Loading state while personas generated
3. Main view: Chat interface with personas discussing
4. User can type in side panel → their input appears as "Guest" message
5. Personas respond to user input naturally
6. User can start new topic anytime

## Architecture

### Frontend (Next.js)
- Single-page app with chat interface
- Main area: Discussion stream (persona messages)
- Side panel: User input (collapsible)
- Topic input page: Form with topic text field + purpose dropdown
- Streaming support for real-time responses

### Backend (Next.js API Routes)
- `/api/topics` - Create new discussion session
- `/api/chat` - Send message, get AI responses
- Session management for conversation history

### AI Layer
- LLM: GPT-4 or Claude for persona responses
- Persona selection: Domain-aware generation based on topic
- Multi-agent orchestration: Sequential or structured轮

## Data Models

### Session
```
- id: string
- topic: string
- purpose: string
- personas: Persona[]
- messages: Message[]
- createdAt: timestamp
```

### Persona
```
- id: string
- name: string
- title: string
- background: string
- expertise: string[]
- perspective: string (optimist, skeptic, realist, etc.)
```

### Message
```
- id: string
- role: "persona" | "user" | "guest"
- personaId?: string
- content: string
- timestamp: timestamp
```

## Tech Stack

- **Frontend:** Next.js, React, Tailwind CSS
- **Backend:** Next.js API Routes
- **AI:** OpenAI GPT-4 API (or Anthropic Claude)
- **State:** React useState/useReducer or React Context

## Error Handling

- Empty topic: Validation error on form
- LLM API failure: Retry with exponential backoff, show error state
- Persona generation fails: Fall back to generic archetypes (researcher, practitioner, critic, etc.)
- Network issues: Graceful degradation with retry option

## Out of Scope (v1)

- User accounts / authentication
- Saving discussion history
- Export/download discussions
- Multiple discussion rooms
- Custom persona creation by users

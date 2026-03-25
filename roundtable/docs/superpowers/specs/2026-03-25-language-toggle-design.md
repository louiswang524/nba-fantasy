# Language Toggle (EN / 中文) — Design Spec

**Date:** 2026-03-25
**Status:** Approved
**Scope:** Add EN / 中文 language selector to the topic form; AI-generated content (personas + discussion turns) responds in the chosen language; TTS uses language-appropriate voices.

---

## Overview

Users can select English or Chinese (Simplified) before starting a discussion. All AI-generated content — persona profiles and discussion turns — is produced in the chosen language. TTS voice assignment filters for Chinese or English voices accordingly. The UI itself remains in English.

---

## Requirements

- EN / 中文 toggle on the topic form (default: EN)
- Personas are generated in the chosen language
- Discussion turns are generated in the chosen language
- TTS voices are filtered by language (`zh-*` for Chinese, `en-*` for English)
- Graceful fallback: if no language-matching voices are available, use any available voice
- No UI translation — only AI-generated content changes language

---

## Architecture

### Data Flow

```
TopicForm
  └─ user selects EN | ZH → language: 'en' | 'zh'
  └─ onSubmit(topic, purpose, people, turns, language)

page.tsx
  └─ stores language state
  └─ passes language to POST /api/session body
  └─ passes language as prop to <ChatInterface language={language} />

/api/session/route.ts
  └─ receives language from request body
  └─ passes to generatePersonas(topic, purpose, count, names, language)
  └─ stores language on Session object

/api/chat/route.ts
  └─ reads session.language
  └─ passes to generateDiscussionTurnStream(..., language)

personas.ts → generatePersonas
  └─ if language === 'zh': append "Respond entirely in Simplified Chinese (简体中文)." to system prompt

chat.ts → generateDiscussionTurnStream
  └─ if language === 'zh': append "Respond entirely in Simplified Chinese (简体中文)." to system prompt

ChatInterface.tsx
  └─ receives language prop
  └─ passes language to tts.assignVoices(count, language)

tts.ts → assignVoices(count, language)
  └─ if language === 'zh': filter voices by v.lang.startsWith('zh')
  └─ if language === 'en': filter voices by v.lang.startsWith('en') (existing behavior)
  └─ fallback: if filtered pool is empty, use all voices
```

---

## File Changes

| File | Change |
|---|---|
| `src/components/TopicForm.tsx` | Add EN/中文 toggle; add `language` to `onSubmit` signature |
| `src/app/page.tsx` | Add `language` state; pass to session API body and ChatInterface |
| `src/types/index.ts` | Add `language: 'en' \| 'zh'` to `Session` type |
| `src/app/api/session/route.ts` | Read `language` from body; pass to `generatePersonas`; store on session |
| `src/lib/personas.ts` | Add `language` param; inject language instruction into system prompt |
| `src/app/api/chat/route.ts` | Read `session.language`; pass to `generateDiscussionTurnStream` |
| `src/lib/chat.ts` | Add `language` param to `generateDiscussionTurnStream`; inject into system prompt |
| `src/components/ChatInterface.tsx` | Add `language` prop; pass to `tts.assignVoices` |
| `src/lib/tts.ts` | Update `assignVoices(count, language)` to filter voices by language |

---

## UI Design

The language toggle is a two-button pill added to `TopicForm`, placed above the podcast length selector:

```
[ EN ]  [ 中文 ]
```

- Selected: gradient violet/fuchsia background (matches existing selected button style)
- Unselected: `bg-white/5` with hover state
- Disabled when `isLoading`
- Default: EN

---

## Prompt Injection

When `language === 'zh'`, append to the system prompt in both `generatePersonas` and `generateDiscussionTurnStream`:

```
Respond entirely in Simplified Chinese (简体中文).
```

When `language === 'en'`, no change to existing prompts.

---

## TTS Voice Assignment

`assignVoices(count: number, language: 'en' | 'zh'): Promise<SpeechSynthesisVoice[]>`

- Filter pool: `v.lang.startsWith('zh')` for Chinese, `v.lang.startsWith('en')` for English
- If filtered pool has fewer voices than `count`, fall back to all available voices
- If all voices pool is empty, return `[]` (browser uses default)

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| No Chinese voices available | Falls back to all voices; TTS plays in default voice |
| LLM ignores language instruction | Accepted — best-effort, no enforcement needed |
| Session missing language field | Defaults to `'en'` in chat route |

---

## Out of Scope

- UI translation (buttons, labels, placeholders remain English)
- Traditional Chinese support
- Per-message language switching
- Language auto-detection from topic text

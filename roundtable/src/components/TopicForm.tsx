'use client';

import { useState } from 'react';
import { Purpose } from '@/types';

interface TopicFormProps {
  onSubmit: (topic: string, purpose: Purpose, people: string[], turns: number, language: 'en' | 'zh') => void;
  isLoading: boolean;
}

export function TopicForm({ onSubmit, isLoading }: TopicFormProps) {
  const [topic, setTopic] = useState('');
  const [purpose, setPurpose] = useState<Purpose>('learning');
  const [peopleInput, setPeopleInput] = useState('');
  const [turns, setTurns] = useState<number>(12);
  const [language, setLanguage] = useState<'en' | 'zh'>('en');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim()) {
      const people = peopleInput
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      onSubmit(topic.trim(), purpose, people, turns, language);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900" />
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PHBhdGggZD0iTTM2IDM0djJoLTJ2LTJoMnptMC00aDJ2MmgtMnYtMnptLTQgNHYyaC0ydi0yaDJ6bTQtOGgydjJoLTJ2LTJ6bS04IDhoMnYyaC0ydi0yek0zMiAyNnYyaC0ydi0yaDJ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-40" />
      
      <div className="relative z-10 w-full max-w-lg px-6">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 mb-6 shadow-2xl shadow-violet-500/30">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">Roundtable</h1>
          <p className="text-slate-400 text-lg">Watch experts debate. Join the conversation.</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white/10 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-3">
              What topic would you like to discuss?
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., The future of AI in healthcare"
              className="w-full px-5 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent focus:bg-white/10 transition-all duration-200"
              disabled={isLoading}
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Who should be at the table?{' '}
              <span className="text-slate-500 font-normal">(optional — comma-separated names)</span>
            </label>
            <input
              type="text"
              value={peopleInput}
              onChange={(e) => setPeopleInput(e.target.value)}
              placeholder="e.g., Marcus Aurelius, Naval Ravikant, Simone de Beauvoir"
              className="w-full px-5 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent focus:bg-white/10 transition-all duration-200"
              disabled={isLoading}
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Language
            </label>
            <div className="flex gap-3">
              {(['en', 'zh'] as const).map((lang) => (
                <button
                  key={lang}
                  type="button"
                  onClick={() => setLanguage(lang)}
                  disabled={isLoading}
                  className={`py-3 px-6 rounded-xl text-sm font-medium transition-all duration-200 ${
                    language === lang
                      ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-500/30'
                      : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  {lang === 'en' ? 'EN' : '中文'}
                </button>
              ))}
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Podcast length
            </label>
            <div className="grid grid-cols-3 gap-3">
              {([
                { label: 'Short', sublabel: '~5 min', turns: 6 },
                { label: 'Medium', sublabel: '~10 min', turns: 12 },
                { label: 'Long', sublabel: '~20 min', turns: 20 },
              ] as const).map((opt) => (
                <button
                  key={opt.turns}
                  type="button"
                  onClick={() => setTurns(opt.turns)}
                  disabled={isLoading}
                  className={`py-3 px-4 rounded-xl text-sm font-medium transition-all duration-200 flex flex-col items-center ${
                    turns === opt.turns
                      ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-500/30'
                      : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <span>{opt.label}</span>
                  <span className="text-xs opacity-70 mt-0.5">{opt.sublabel}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="mb-8">
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Purpose
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(['entertainment', 'learning', 'decision-making'] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPurpose(p)}
                  disabled={isLoading}
                  className={`py-3 px-4 rounded-xl text-sm font-medium transition-all duration-200 ${
                    purpose === p
                      ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-500/30'
                      : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  {p === 'entertainment' ? '🎭 Fun' : p === 'learning' ? '📚 Learn' : '🎯 Decide'}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !topic.trim()}
            className="w-full py-4 px-6 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold rounded-xl hover:from-violet-500 hover:to-fuchsia-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-violet-500/30 hover:shadow-violet-500/50 transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Starting Discussion...
              </span>
            ) : (
              'Start Discussion'
            )}
          </button>
        </form>

        <p className="text-center text-slate-500 text-sm mt-6">
          AI-generated experts discuss from multiple viewpoints
        </p>
      </div>
    </div>
  );
}

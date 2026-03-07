import { Message } from '@/types';

interface MessageBubbleProps {
  message: Message;
}

const personaColors: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  '1': { bg: 'from-violet-500/20 to-violet-600/10', border: 'border-violet-500/30', text: 'text-violet-300', dot: 'bg-violet-400' },
  '2': { bg: 'from-fuchsia-500/20 to-fuchsia-600/10', border: 'border-fuchsia-500/30', text: 'text-fuchsia-300', dot: 'bg-fuchsia-400' },
  '3': { bg: 'from-cyan-500/20 to-cyan-600/10', border: 'border-cyan-500/30', text: 'text-cyan-300', dot: 'bg-cyan-400' },
  '4': { bg: 'from-amber-500/20 to-amber-600/10', border: 'border-amber-500/30', text: 'text-amber-300', dot: 'bg-amber-400' },
};

export function MessageBubble({ message }: MessageBubbleProps) {
  const isPersona = message.role === 'persona';
  const isGuest = message.role === 'guest';
  
  const colorKey = message.personaId?.replace('persona-', '') || '1';
  const colors = personaColors[colorKey] || personaColors['1'];

  if (isPersona) {
    return (
      <div className="flex gap-4 animate-fade-in-up">
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colors.bg} border ${colors.border} flex items-center justify-center flex-shrink-0 shadow-lg`}>
          <span className={`text-lg font-bold ${colors.text}`}>
            {message.personaName?.charAt(0) || 'E'}
          </span>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`font-semibold ${colors.text}`}>{message.personaName}</span>
            <span className="text-slate-500 text-sm">•</span>
            <span className="text-slate-400 text-sm capitalize">{message.perspective}</span>
          </div>
          <div className={`bg-gradient-to-br ${colors.bg} border ${colors.border} rounded-2xl p-4`}>
            <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>
        </div>
      </div>
    );
  }

  if (isGuest) {
    return (
      <div className="flex gap-4 animate-fade-in-up ml-auto max-w-[80%]">
        <div className="flex-1">
          <div className="flex items-center justify-end gap-2 mb-2">
            <span className="text-emerald-400 font-semibold">You</span>
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
          </div>
          <div className="bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 rounded-2xl p-4">
            <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>
        </div>
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center flex-shrink-0">
          <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      </div>
    );
  }

  return null;
}

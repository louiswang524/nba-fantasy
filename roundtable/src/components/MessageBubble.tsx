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

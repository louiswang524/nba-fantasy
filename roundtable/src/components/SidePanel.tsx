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

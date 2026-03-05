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

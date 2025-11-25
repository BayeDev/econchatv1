'use client';

import { SUGGESTED_QUERIES } from '@/lib/constants';
import { Sparkles } from 'lucide-react';

interface SuggestedQueriesProps {
  onSelect: (query: string) => void;
}

export default function SuggestedQueries({ onSelect }: SuggestedQueriesProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-text-secondary">
        <Sparkles className="w-4 h-4" />
        <span className="text-sm">Try asking about:</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {SUGGESTED_QUERIES.map((query, index) => (
          <button
            key={index}
            onClick={() => onSelect(query)}
            className="px-3 py-2 bg-surface-light hover:bg-border text-text-secondary hover:text-text-primary rounded-lg text-sm transition-colors text-left"
          >
            {query}
          </button>
        ))}
      </div>
    </div>
  );
}
